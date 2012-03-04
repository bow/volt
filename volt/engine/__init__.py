# -*- coding: utf-8 -*-
"""
-----------
volt.engine
-----------

Base Unit, Engines, and Pagination classes.

Units represent a resource used in the generated site, such as a blog post
or an image. Engines are classes that perform initial processing of Unit
objects. Paginations are groups of several Units that will be written to a single
HTML file, for example blog posts written in February 2009.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""

import codecs
import glob
import os
import re
from datetime import datetime
from functools import partial

import yaml

from volt import ContentError, ParseError
from volt.config import CONFIG, SessionConfig
from volt.util import grab_class


# regex objects, so compilation is done efficiently
# for TextUnit header delimiter
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
# for Engine.slugify
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


class Engine(object):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each Unit. This base engine class does not perform any processing by
    itself, but provides convenient Unit processing methods for the
    subclassing engine.

    Subclassing classes must override the ``parse`` and ``write`` methods
    of the base engine class.

    """

    def __init__(self, session_config=CONFIG):
        """Initializes the engine.

        Keyword Args:
            session_config - SessionConfig instance from volt.config,
                defaults to CONFIG.

        """
        if not isinstance(session_config, SessionConfig):
            raise TypeError("Engine objects must be initialized with "
                            "a SessionConfig instance.")

        self.CONFIG = session_config
        self.units = []

    def globdir(self, directory, pattern='*', is_gen=False):
        """Returns glob or iglob results for a given directory.

        Args:
            directory - Absolute path of the directory to glob.

        Keyword Args:
            pattern - File name pattern to search in the glob directory,
                defaults to all files ('*').
            is_gen - Boolean indicating whether to return a generator or a list.

        """
        pattern = os.path.join(directory, pattern)
        if is_gen:
            return glob.iglob(pattern)

        return glob.glob(pattern)

    def set_unit_paths(self, unit, base_dir, base_url='', set_index_html=True):
        """Sets the permalink and absolute file path for the given unit.

        Args:
            unit - Unit instance whose path and URL are to be set
            base_dir - Absolute file system path to the output site directory

        Keyword Args:
            base_url - Base url to be set for the permalink, defaults to an empty
                string so permalinks are relative
            index_html -  Boolean indicating output file name;  if False then
                the output file name is '%s.html' where %s is the last
                string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows nice URLs without fiddling
        with .htaccess too much.

        """
        url = [base_url]
        path = [base_dir]

        # set permalink
        # we don't want double slashes in URL, so remove empty strings
        url.extend(filter(None, unit.permalist))
        # if index_html is False, then we have to refer to the file
        # directly in the permalink
        if set_index_html:
            url[-1] = url[-1] + '/'
        else:
            url[-1] = url[-1] + '.html'
        setattr(unit, 'permalink', '/'.join(url))

        # set absolute path
        path.extend(unit.permalist)
        if set_index_html:
            path.append('index.html')
        else:
            path[-1] = path[-1] + '.html'
        setattr(unit, 'path', os.path.join(*(path)))

    def process_text_units(self, config):
        """Processes units into a TextUnit object and returns them in a list.

        Args:
            config - Config object corresponding to the engine settings,
                e.g. config.BLOG for the BlogEngine or config.PLAIN
                for the PlainEngine.

        """
        # get absolute paths of content files
        units = []
        content_dir = self.globdir(config.CONTENT_DIR, is_gen=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # parse each file and fill self.contents with TextUnit-s
        # also set its URL and absolute file path to be written
        for fname in files:
            units.append(TextUnit(fname, config))
            # paths and permalinks are not set in TextUnit to facillitate
            # testing; ideally, each xUnit should only be using one Config instance
            self.set_unit_paths(units[-1], self.CONFIG.VOLT.SITE_DIR)

        return units

    def sort_units(self, units, sort_key):
        """Sorts a list of units according to the given header field value.

        Args:
            units - List containing units to sort
            sort_key - String of field name indicating the key used for
                sorting, if preceeded with  a dash ('-') then sorting is
                reversed.

        """
        reversed = sort_key.startswith('-')
        sort_key = sort_key.strip('-')
        units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)

    def chain_units(self, units):
        """Sets the previous and next permalink attributes of units in a list.

        Args:
            units - List containing units to chain

        This method allows each unit in a list to link to its previous and/or
        next unit according to the ordering in the list.

        """
        for idx, unit in enumerate(units):
            if idx != 0:
                setattr(unit, 'permalink_prev', self.units[idx-1].permalink)
            if idx != len(self.units) - 1:
                setattr(unit, 'permalink_next', self.units[idx+1].permalink)

    def build_packs(self, pack_list):

        packs = dict()

        for pack in pack_list:

            base_permalist = re.findall(_RE_PERMALINK, pack.strip('/') + '/')
            if base_permalist == []:
                # pagination for all items
                unit_groups = [self.units]
                for units in unit_groups:
                    packs[''] = Pack(units, base_permalist)

            else:
                field_token_idx = [base_permalist.index(token) for token in base_permalist if \
                        token.startswith('{') and token.endswith('}')].pop(0)
                field = base_permalist[field_token_idx][1:-1]

                if ':' in field:
                    field, strftime = field.split(':')
                    # get all the date.strftime tokens in a list
                    date_tokens = strftime.strip('/').split('/')
                    # get all datetime fields from units
                    datetime_per_unit = [getattr(x, field) for x in self.units]
                    # construct set of all datetime combinations in self.units
                    # according to the user's supplied pagination URL
                    # e.g. if URL == '%Y/%m' and there are two units with 2009/10
                    # and one with 2010/03 then
                    # all_items == set([('2009', '10), ('2010', '03'])
                    all_items = set(zip(*[[x.strftime(y) for x in datetime_per_unit] \
                            for y in date_tokens]))

                    for item in all_items:
                        unit_groups = [x for x in self.units if \
                                zip(*[[getattr(x, field).strftime(y)] for y in date_tokens])[0] == item]
                        base_permalist[field_token_idx:] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

                elif isinstance(getattr(self.units[0], field), basestring):
                    all_items = set([getattr(x, field) for x in self.units])
                    for item in all_items:
                        unit_groups = [x for x in self.units if item == getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

                # pagination for all item if field is list or tuple
                elif isinstance(getattr(self.units[0], field), (list, tuple)):
                    # append empty string to pagination URL as placeholder for list item
                    # get item list for each unit
                    item_list_per_unit = (getattr(x, field) for x in self.units)
                    # get unique list item in all units
                    all_items = reduce(set.union, [set(x) for x in item_list_per_unit])
                    # iterate and paginate over each unique list item
                    for item in all_items:
                        unit_groups = [x for x in self.units if item in getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

        return packs

    def write_output(self, file_obj, string):
        """Writes string to the open file object.

        Args:
            file_obj - Opened fie object
            string - String to write

        This is written to facillitate testing of the calling method.

        """
        file_obj.write(string.encode('utf-8'))

    def write_units(self, template_path):
        """Writes single units into the given output file.

        Args:
            template_path - Template file name, must exist in the defined template
                directory.
        """
        template_file = os.path.basename(template_path)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for unit in self.units:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexptected results
            if os.path.exists(unit.path):
                # TODO: find a better exception name
                raise ContentError("'%s' already exists!" % unit.path)
            os.makedirs(os.path.dirname(unit.path))
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, site=self.CONFIG.SITE)
                self.write_output(target, rendered)

    def write_packs(self, template_path):

        template_file = os.path.basename(template_path)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for pack in self.packs:
            for pagination in self.packs[pack].paginations:
                # warn if files are overwritten
                # this indicates a duplicate post, which could result in
                # unexptected results
                if os.path.exists(pagination.path):
                    # TODO: find a better exception name
                    raise ContentError("'%s' already exists!" % pagination.path)
                # !!!
                # this could be dangerous, check later
                try:
                    os.makedirs(os.path.dirname(pagination.path))
                except OSError:
                    pass
                with open(pagination.path, 'w') as target:
                    # since pack object only stores indexes of unit in self.unit
                    # we need to get the actual unit items before writing
                    rendered = template.render(page=pagination.__dict__, site=self.CONFIG.SITE)
                    self.write_output(target, rendered)

    def parse(self):
        """Performs initial processing of resources into unit objects."""
        raise NotImplementedError("Engine subclass must implement a run method.")

    def write(self):
        """Write processed units into the output file."""
        raise NotImplementedError("Engine subclass must implement a write method.")


class Unit(object):

    """Base Volt Unit class.

    The unit class represent a single resource used for generating the site,
    such as a blog post, an image, or a regular plain text file.

    """

    def __init__(self, id):
        """Initializes a unit instance.

        Args:
            id - String that refers exclusively to the unit. For example,
                if the resource is a text file then id can be the file path.

        """
        self.id = id

    def __repr__(self):
        return str(self.__dict__)

    @property
    def fields(self):
        """Returns the unit namespace."""
        return self.__dict__.keys()

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime
    get_display_time = datetime.strftime

    def parse_yaml(self, string):
        """Parses the YAML string into a dictionary object.

        Args:
            string - YAML-formatted string

        This is a thin wrapper for yaml.load, so it's more convenient
        for subclassing unit classes to parse YAML contents.

        """
        # why can't this be assigned directly like the other wrappers?
        return yaml.load(string)

    def check_protected(self, field, prot):
        """Checks if the given field can be set by the user or not.
        
        Args:
            field - String to check against the list containing protected fields.
            prot - Iterable containing protected fields.

        """
        if field in prot:
            raise ContentError("'%s' should not define the protected header "
                               "field '%s'" % (self.id, field))

    def check_required(self, req):
        """Checks if all the required header fields are present.

        Args:
            req -  Iterable that returns required header fields.

        """
        for field in req:
            if not hasattr(self, field):
                raise ContentError("Required header field '%s' is missing "
                                   "in '%s'." % (field, self.id))

    def as_list(self, field, sep):
        """Transforms a comma-separated tags or categories string into a list.

        Args:
            fields - String to transform into list.
            sep - String used to split fields into list.

        """
        return list(set(filter(None, field.strip().split(sep))))

    def slugify(self, string):
        """Returns a slugified version of the given string.

        Args:
            string - String to transform into slug.

        """
        string = string.strip()

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, bad chars, and dashes in front and end
        string = re.sub(_RE_PRUNE, '', string)

        # raise exception if there are non-ascii chars
        try:
            string.decode('ascii')
        except UnicodeDecodeError:
            raise ContentError("Slug in '%s' contains non-ascii characters." \
                               % self.id)

        # slug should not begin or end with dash or contain multiple dashes
        string = re.sub(_RE_MULTIPLE, '-', string)

        # and finally, we string preceeding and succeeding dashes
        string = string.lower().strip('-')

        # raise exception if slug results in an empty string
        if not string:
            raise ContentError("Slug for '%s' is an empty string." % self.id)

        return string

    def get_permalist(self, pattern, unit_base_url='/'):
        """Returns a list of strings which will be used to construct permalinks.

        Args:
            pattern - String replacement pattern.

        Keyword Args:
            unit_base_url - Base URL of the engine, to be appended in front of each
                unit URL.

        The pattern argument may refer to the current object's attributes by
        enclosing them in square brackets. If the referred instance attribute 
        is a datetime object, it must be formatted by specifying a string format
        argument.

        Several examples of a valid permalink pattern:
        
        '{time:%Y/%m/%d}/{slug}'
            Returns, for example, ['2009', '10', '04', 'the-slug']

        '{time:%Y}/post/{time:%d}/blog/{id}'
            Returns, for example,  ['2009', 'post', '04', 'blog', 'item-103']

        """
        # strip preceeding '/' but make sure ends with '/'
        pattern = pattern.strip('/') + '/'

        # get all permalink components and store into list
        perms = re.findall(_RE_PERMALINK, pattern)

        # process components that are enclosed in {}
        permalist = []
        for item in perms:
            if item[0] == '{' and item[-1] == '}':
                cmp = item[1:-1]
                if ':' in cmp:
                    cmp, fmt = cmp.split(':')
                if not hasattr(self, cmp):
                    raise ContentError("'%s' has no '%s' attribute." % \
                            (self.id, cmp))
                if isinstance(getattr(self, cmp), datetime):
                    strftime = datetime.strftime(getattr(self, cmp), fmt)
                    permalist.extend(filter(None, strftime.split('/')))
                else:
                    permalist.append(self.slugify(getattr(self, cmp)))
            else:
                permalist.append(self.slugify(item))

        return [unit_base_url.strip('/')] + filter(None, permalist)


class TextUnit(Unit):

    """Class representation of text resources.

    This unit represents resources whose metadata (YAML header) is contained
    in the same file as the content. Some examples of resources like this 
    is a single blog post or a single plain page. 

    """

    def __init__(self, fname, conf, delim=_RE_DELIM):
        """Initializes TextUnit.

        Args:
            fname - Absolute path to the source file.
            conf - Config object containing unit options.

        Keyword Args:
            delim - Compiled regex object used for parsing the header.

        """
        super(TextUnit, self).__init__(fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, delim.split(source.read()))
            # header should be parsed by yaml into dict
            header = self.parse_yaml(read.pop(0))
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, conf.PROTECTED)
                if field in conf.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], conf.CONTENT_DATETIME_FORMAT)
                if field in conf.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], conf.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])

            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(conf.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        # and set global values
        for field in conf.GLOBAL_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, conf.GLOBAL_FIELDS[field])

        # set permalink components
        self.permalist = self.get_permalist(conf.PERMALINK, conf.URL)
        # set displayed time string
        if hasattr(self, 'time'):
            self.display_time = self.time.strftime(conf.DISPLAY_DATETIME_FORMAT)


class Pack(object):
    """Packs are URL sections
    """
    def __init__(self, unit_matches, base_permalist):

        self.paginations = []

        # construct permalist components, relative to blog URL
        base_permalist = filter(None, [CONFIG.BLOG.URL] + base_permalist)

        units_per_pack = CONFIG.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_matches) / units_per_pack + \
                (len(unit_matches) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                self.paginations.append(Pagination(unit_matches[start:stop], \
                        i, base_permalist, config=CONFIG))
            else:
                self.paginations.append(Pagination(unit_matches[start:], \
                        i, base_permalist, is_last=True, config=CONFIG))


class Pagination(object):

    """TODO
    """

    def __init__(self, units, pack_idx, base_permalist=[], title='',
            is_last=False, config=CONFIG):
        """Initializes a Pagination instance.

        Args:
            units - List containing units to pack.
            pack_idx - Current pack object index.

        Keyword Args:
            base_permalist - List of URL components common to all pack
                permalinks.
            is_last - Boolean indicating whether this pack is the last one.
            config - SessionConfig instance.

        """
        self.title = title
        self.units = units
        # because page are 1-indexed and lists are 0-indexed
        self.pack_idx = pack_idx + 1
        # this will be appended for pack_idx > 1, e.g. .../page/2
        # precautions for empty string, so double '/'s are not introduced
        base_permalist = filter(None, base_permalist)

        if self.pack_idx == 1:
            # if it's the first pack page, use base_permalist only
            self.permalist = base_permalist
        else:
            # otherwise add pagination dir and pack index
            self.permalist = base_permalist + filter(None, [config.SITE.PAGINATION_URL,\
                    str(self.pack_idx)])

        # path is path to folder + index.html
        path = [config.VOLT.SITE_DIR] + self.permalist + ['index.html']
        self.path = os.path.join(*(path))

        url = [''] + self.permalist
        self.permalink = '/'.join(url) + '/'

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        pagination_url = [''] + base_permalist
        # next permalinks
        if not is_last:
            self.permalink_next = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx + 1)])) + '/'
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(pagination_url) + '/'
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx - 1)])) + '/'


get_engine = partial(grab_class, cls=Engine)
