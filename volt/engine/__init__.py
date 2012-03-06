# -*- coding: utf-8 -*-
"""
-----------
volt.engine
-----------

Base Unit, Engine, Pack, and Pagination classes.

Units represent a resource used in the generated site, such as a blog post
or an image. Engines are classes that perform initial processing of Unit
objects. Packs represent a collection of Units sharing similar attributes.
Paginations are groups of several Units that will be written to a single
HTML file, for example blog posts written in February 2009.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import codecs
import glob
import os
import re
from datetime import datetime
from functools import partial

import yaml

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


class DuplicateOutputError(Exception):
    """Raised when Volt tries to overwrite an existing HTML output file.

    This is an exception because in a normal Volt run, there should be no
    duplicate output file. Each unit and pack should have its own unique
    absolute path.

    """
    pass

class ContentError(Exception):
    """Base exception for content-related error."""
    pass

class HeaderFieldError(ContentError):
    """Raised if a unit header field defines a protected field."""
    pass

class PermalinkTemplateError(ContentError):
    """Raised if a header field value defined in the permalink template is not found."""
    pass

class ParseError(ContentError):
    """Raised if a content-parsing related error occurs."""
    pass


class Engine(object):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each unit. This base engine class does not perform any processing by
    itself, but provides convenient unit processing methods for the
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
        self.units = list()
        self.packs = dict()

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

    def set_unit_paths(self, unit, base_dir, index_html_only=True):
        """Sets the permalink and absolute file path for the given unit.

        Args:
            unit - Unit instance whose path and URL are to be set
            base_dir - Absolute file system path to the output site directory

        Keyword Args:
            index_html_only -  Boolean indicating output file name;  if False
                then the output file name is '%s.html' where %s is the last
                string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows for nice URLs without fiddling
        with .htaccess too much.

        """
        path = [base_dir]
        abs_url = self.CONFIG.SITE.URL
        rel_url = ['']

        # set path and urls
        path.extend(unit.permalist)
        rel_url.extend(filter(None, unit.permalist))
        if index_html_only:
            rel_url[-1] = rel_url[-1] + '/'
            path.append('index.html')
        else:
            rel_url[-1] = rel_url[-1] + '.html'
            path[-1] = path[-1] + '.html'
        setattr(unit, 'permalink', '/'.join(rel_url))
        setattr(unit, 'permalink_abs', '/'.join([abs_url] + rel_url[1:]).strip('/'))
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
            self.set_unit_paths(units[-1], base_dir=self.CONFIG.VOLT.SITE_DIR, \
                    index_html_only=self.CONFIG.SITE.INDEX_HTML_ONLY)

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

    def build_packs(self, pack_patterns, units):
        """Build packs of units and return them in a dictionary.

        Args:
            pack_patterns - List containing packs patterns to build.

        This method will expand the supplied pack_pattern according to
        the values present in all units. For example, if the pack_pattern
        is '{time:%Y}' and there are ten posts written with a 2010 year,
        build_pack will return a dictionary containing one entry with '2010'
        as the key and a Pack object containing the ten posts as the value.

        """
        # dictionary to contain all built packs
        packs = dict()

        for pack in pack_patterns:

            # get all tokens in the pack pattern
            base_permalist = re.findall(_RE_PERMALINK, pack.strip('/') + '/')

            # if token is not set, build pack for all units
            if base_permalist == []:
                unit_groups = [units]
                for units in unit_groups:
                    packs[''] = Pack(units, base_permalist, config=self.CONFIG)

            else:
                # get the index of the field token to replace
                field_token_idx = [base_permalist.index(token) for token in \
                        base_permalist if token.startswith('{') and \
                        token.endswith('}')].pop(0)
                # and discard the curly braces
                field = base_permalist[field_token_idx][1:-1]

                # ':' should only be present if the field value is a datetime
                # object
                if ':' in field:
                    # separate the field name from the datetime formatting
                    field, strftime = field.split(':')
                    # get all the date.strftime tokens in a list
                    date_tokens = strftime.strip('/').split('/')
                    # get all datetime fields from units
                    datetime_per_unit = [getattr(x, field) for x in units]
                    # construct set of all datetime combinations in units
                    # according to the user's supplied pagination URL
                    # e.g. if URL == '%Y/%m' and there are two units with 2009/10
                    # and one with 2010/03 then
                    # all_items == set([('2009', '10), ('2010', '03'])
                    all_items = set(zip(*[[x.strftime(y) for x in datetime_per_unit] \
                            for y in date_tokens]))

                    # now build the pack for each time points
                    for item in all_items:
                        # get all units whose datetime values match 'item'
                        unit_groups = [x for x in units if \
                                zip(*[[getattr(x, field).strftime(y)] for y in date_tokens])[0] == item]
                        # the base permalist if the pack URL tokens
                        base_permalist[field_token_idx:] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist, config=self.CONFIG)

                # similar logic as before, but this time for string field values
                # much simpler
                elif isinstance(getattr(units[0], field), basestring):
                    # get a set of all string values
                    all_items = set([getattr(x, field) for x in units])
                    for item in all_items:
                        unit_groups = [x for x in units if item == getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist, config=self.CONFIG)

                # and finally for list or tuple field values
                elif isinstance(getattr(units[0], field), (list, tuple)):
                    # get item list for each unit
                    item_list_per_unit = (getattr(x, field) for x in units)
                    # get unique list item in all units
                    all_items = reduce(set.union, [set(x) for x in item_list_per_unit])
                    # iterate and paginate over each unique list item
                    for item in all_items:
                        unit_groups = [x for x in units if item in getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist, config=self.CONFIG)

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
                raise DuplicateOutputError("'%s' already exists." % unit.path)
            try:
                os.makedirs(os.path.dirname(unit.path))
            except OSError:
                pass
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, CONFIG=self.CONFIG)
                self.write_output(target, rendered)

    def write_packs(self, template_path):
        """Writes packs into the given output file.

        Args:
            template_path - Template file name, must exist in the defined template
                directory.

        """
        template_file = os.path.basename(template_path)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for pack in self.packs:
            for pagination in self.packs[pack].paginations:
                # warn if files are overwritten
                # this indicates a duplicate post, which could result in
                # unexptected results
                if os.path.exists(pagination.path):
                    raise DuplicateOutputError("'%s' already exists." % pagination.path)
                # !!!
                # this could be dangerous, check later
                try:
                    os.makedirs(os.path.dirname(pagination.path))
                except OSError:
                    pass
                with open(pagination.path, 'w') as target:
                    # since pack object only stores indexes of unit in self.unit
                    # we need to get the actual unit items before writing
                    rendered = template.render(page=pagination.__dict__, CONFIG=self.CONFIG)
                    self.write_output(target, rendered)

    def activate(self):
        """Performs initial processing of resources into unit objects."""
        raise NotImplementedError("Engine subclass must implement an activate method.")

    def dispatch(self):
        """Performs final processing after all plugins are run."""
        raise NotImplementedError("Engine subclass must implement a dispatch method.")


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
            raise HeaderFieldError("'%s' should not define the protected "
                               " header field '%s'" % (self.id, field))

    def check_required(self, req):
        """Checks if all the required header fields are present.

        Args:
            req -  Iterable that returns required header fields.

        """
        for field in req:
            if not hasattr(self, field):
                raise HeaderFieldError("Required header field '%s' is "
                                   "missing in '%s'." % (field, self.id))

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

        'post/{time:%d}/{id}'
            Returns, for example,  ['post', '04', 'item-103']

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
                    raise PermalinkTemplateError("'%s' has no '%s' attribute." % \
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
            try:
                header = self.parse_yaml(read.pop(0))
            except IndexError:
                raise ParseError("Header not detected in '%s'." % fname)
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


class Pagination(object):

    """Class representing a single paginated HTML file.

    The pagination class computes the necessary attributes required to write
    a single HTML file containing the desired units. It is the __dict__ object
    of this Pagination class that will be passed on to the template writing
    environment. However, the division of which units go to which pagination
    page is done by another class instantiating Pagination, for example the
    Pack class.

    """

    def __init__(self, units, pack_idx, base_permalist=[], title='',
            is_last=False, config=CONFIG, index_html_only=True):
        """Initializes a Pagination instance.

        Args:
            units - List containing units to pack.
            pack_idx - Current pack object index.

        Keyword Args:
            title - String denoting the title of the pagination page.
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

        # set path and url
        path = [config.VOLT.SITE_DIR]
        path.extend(self.permalist)
        url = [''] + self.permalist
        if index_html_only:
            path.append('index.html')
            url[-1] = url[-1] + '/'
        else:
            path[-1] = path[-1] + '.html'
            url[-1] = url[-1] + '.html'
        setattr(self, 'path', os.path.join(*(path)))
        setattr(self, 'permalink', '/'.join(url))

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        pagination_url = [''] + base_permalist
        # next permalinks
        if not is_last:
            self.permalink_next = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx + 1)]))
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(pagination_url)
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx - 1)]))

        # set final chain permalink url according to index_html_only
        if hasattr(self, 'permalink_next'):
            if index_html_only:
                self.permalink_next += '/'
            else:
                self.permalink_next += '.html'

        if hasattr(self, 'permalink_prev'):
            if index_html_only:
                self.permalink_prev += '/'
            else:
                self.permalink_prev += '.html'


class Pack(object):

    """Pack represent a collection of units sharing a similar field value.

    The pack class is used mainly to create sub-sections of an Engine as
    denoted by its URL. For example, if we are creating a blog using Volt,
    we might want to have a page containing all posts with the 'foo' tag,
    or perhaps a page containing all posts written in January 2011. In these
    two cases, pack will be an object representing all posts whose tag contains
    'foo' or all posts whose datetime.year is 2011 and datetime.month is 1,
    respectively.

    Of course, listing all possible units sharing a given field value might
    not be practical if there are hundreds of units. That's why Pack can also
    handle paginating these units into HTML files with the desired number of
    units per page. Pack does this by using the Pagination class, which is
    a class that represents single HTML pages in a Pack. See Pagination's
    documentation for more information.

    """

    def __init__(self, unit_matches, base_permalist, \
            pagination_class=Pagination, config=CONFIG):
        """Initializes a Pack object.

        Args:
            unit_matches - List of all units sharing a certain field value.
            base_permalist - Permalink tokens that will be used by all
                paginations of the given units.

        Keyword Args:
            pagination_class - Pagination class to use. Most of the time,
                the base Pagination class is sufficient.
            config - SessionConfig object.

        Selection of the units to pass on to initialize Pack is done by an
        Engine object. An example of method that does this in the base Engine
        class is the build_packs method.

        """
        # list to contain all paginations
        self.paginations = []

        # construct permalist tokens, relative to blog URL
        base_permalist = filter(None, [config.BLOG.URL] + base_permalist)

        units_per_pagination = config.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_matches) / units_per_pagination + \
                (len(unit_matches) % units_per_pagination != 0)

        # construct pagination bjects for each pagination page
        for i in range(pagination):
            start = i * units_per_pagination
            if i != pagination - 1:
                stop = (i + 1) * units_per_pagination
                self.paginations.append(pagination_class(\
                        unit_matches[start:stop], i, \
                        base_permalist, title='', config=config, \
                        index_html_only=config.SITE.INDEX_HTML_ONLY))
            else:
                self.paginations.append(pagination_class(\
                        unit_matches[start:], i, \
                        base_permalist, title='', is_last=True, config=config, \
                        index_html_only=config.SITE.INDEX_HTML_ONLY))


get_engine = partial(grab_class, cls=Engine)
