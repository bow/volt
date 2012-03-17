# -*- coding: utf-8 -*-
"""
----------------
volt.engine.core
----------------

Volt core engine classes.

Contains the Engine, Unit, Pagination, Pack, and Page classes.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import codecs
import os
import re
import sys
import warnings
from datetime import datetime
from functools import partial

import yaml

from volt.config import CONFIG, Config
from volt.exceptions import HeaderFieldError, ContentError, ConfigError, \
                            PermalinkTemplateError, DuplicateOutputError, \
                            EmptyUnitsWarning
from volt.utils import path_import


# regex objects for unit header and permalink processing
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


class Engine(object):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each unit. This base engine class does not perform any processing by
    itself, but provides convenient unit processing methods for the
    subclassing engine.

    Subclassing classes must override the activate and dispatch methods of the
    base Engine class.

    """

    DEFAULTS = Config()

    USER_CONF_ENTRY = None

    def __init__(self):
        """Initializes the engine."""
        self.units = list()
        self.packs = list()
        self.config = Config(self.DEFAULTS)

    def activate(self):
        """Performs initial processing of resources into unit objects."""
        raise NotImplementedError("%s must implement an activate method." % \
                self.__class__.__name__)

    def dispatch(self):
        """Performs final processing after all plugins are run."""
        raise NotImplementedError("%s must implement a dispatch method." % \
                self.__class__.__name__)

    def prime(self):
        """Consolidates default engine Config and user-defined Config.

        In addition to consolidating Config values, this method also sets
        the values of CONTENT_DIR, and *_TEMPLATE to absolute directory paths.

        """
        if self.USER_CONF_ENTRY is None:
            raise ConfigError("%s must define a 'USER_CONF_ENTRY' value as a "
                              "class attribute." % self.__class__.__name__)

        if not hasattr(self.config, 'CONTENT_DIR'):
            raise ConfigError("%s must define a 'CONTENT_DIR' value in "
                              "DEFAULTS." % self.__class__.__name__)

        # get user config object
        conf_name = os.path.splitext(os.path.basename(CONFIG.VOLT.USER_CONF))[0]
        voltconf = path_import(conf_name, CONFIG.VOLT.ROOT_DIR)
        user_config = getattr(voltconf, self.USER_CONF_ENTRY)

        # to ensure proper Config consolidation
        if not isinstance(user_config, Config):
            raise TypeError("User Config object '%s' must be a Config instance." % \
                    self.USER_CONF_ENTRY)

        self.config.update(user_config)

        # set absolute directory paths
        self.config.CONTENT_DIR = os.path.join(CONFIG.VOLT.CONTENT_DIR, \
                self.config.CONTENT_DIR)

        for template in [x for x in self.config.keys() if x.endswith('_TEMPLATE')]:
                self.config[template] = os.path.join(CONFIG.VOLT.TEMPLATE_DIR, \
                        self.config[template])

    def sort_units(self, sort_key):
        """Sorts a list of units according to the given header field name.

        Args:
            sort_key - String of field name indicating the key used for
                sorting, if preceeded with  a dash ('-') then sorting is
                reversed.

        """
        reversed = sort_key.startswith('-')
        sort_key = sort_key.strip('-')
        try:
            self.units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)
        except AttributeError:
            raise HeaderFieldError("Sorting key '%s' not present in all unit "
                                   "header field." % sort_key)

    def chain_units(self):
        """Sets the previous and next permalink attributes of units.

        This method allows each unit in a list to link to its previous and/or
        next unit according to the ordering.

        """
        try:
            for idx, unit in enumerate(self.units):
                if idx != 0:
                    setattr(unit, 'permalink_prev', self.units[idx-1].permalink)
                if idx != len(self.units) - 1:
                    setattr(unit, 'permalink_next', self.units[idx+1].permalink)
        except AttributeError:
            raise ContentError("Unit '%s' neighbor(s) does not have a "
                               "permalink attribute." % unit.id)

    def _packer_all(self, field, base_permalist, units_per_pagination):
        """Build packs for all field values (PRIVATE)."""
        yield Pack(self.units, base_permalist, units_per_pagination)

    def _packer_single(self, field, base_permalist, units_per_pagination):
        """Build packs for string/int/float header field values (PRIVATE)."""
        units = self.units
        str_set = set([getattr(x, field) for x in units])

        for item in str_set:
            matches = [x for x in units if item == getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            yield Pack(matches, base_permalist, units_per_pagination)

    def _packer_multiple(self, field, base_permalist, units_per_pagination):
        """Build packs for list or tuple header field values (PRIVATE)."""
        units = self.units
        item_list_per_unit = (getattr(x, field) for x in units)
        item_set = reduce(set.union, [set(x) for x in item_list_per_unit])

        for item in item_set:
            matches = [x for x in units if item in getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            yield Pack(matches, base_permalist, units_per_pagination)

    def _packer_datetime(self, field, base_permalist, units_per_pagination):
        """Build packs for datetime header field values (PRIVATE)."""
        units = self.units
        # separate the field name from the datetime formatting
        field, time_fmt = field.split(':')
        time_tokens = time_fmt.strip('/').split('/')
        unit_times = [getattr(x, field) for x in units]
        # construct set of all datetime combinations in units according to
        # the user's supplied pagination URL; e.g. if URL == '%Y/%m' and
        # there are two units with 2009/10 and one with 2010/03 then
        # time_set == set([('2009', '10), ('2010', '03'])
        time_strs = [[x.strftime(y) for x in unit_times] for y in time_tokens]
        time_set = set(zip(*time_strs))

        # create placeholders for new tokens
        base_permalist = base_permalist[:-1] + [None] * len(time_tokens)
        for item in time_set:
            # get all units whose datetime values match 'item'
            matches = []
            for unit in units:
                val = getattr(unit, field)
                time_str = [[val.strftime(y)] for y in time_tokens]
                time_tuple = zip(*time_str)
                assert len(time_tuple) == 1
                if item in time_tuple:
                    matches.append(unit)

            base_permalist = base_permalist[:-(len(time_tokens))] + list(item)
            yield Pack(matches, base_permalist, units_per_pagination)

    def build_packs(self, pack_patterns):
        """Build packs of units and return them in a list.

        Args:
            pack_patterns - List containing packs patterns to build.

        This method will expand the supplied pack_pattern according to
        the values present in all units. For example, if the pack_pattern
        is '{time:%Y}' and there are five units with a datetime.year attribute
        2010 and another five with 2011, build_pack will return a list
        containing two Pack objects, representing 2010 and 2011 respectively.

        """
        try:
            base_url = self.config.URL.strip('/')
        except AttributeError:
            raise ConfigError("%s Config must define a 'URL' value if "
                              "build_packs() is used." % \
                              self.__class__.__name__)
        try:
            units_per_pagination = self.config.POSTS_PER_PAGE
        except AttributeError:
            raise ConfigError("%s Config must define a 'POSTS_PER_PAGE' value "
                              "if build_packs() is used." % \
                              self.__class__.__name__)

        # build_packs operates on self.units
        units = self.units
        if not units:
            warnings.warn("%s has no units to pack." % self.__class__.__name__, \
                    EmptyUnitsWarning)

        # list to contain all built packs
        packs = list()
        packer_map = {'all': self._packer_all,
                      'str': self._packer_single,
                      'int': self._packer_single,
                      'float': self._packer_single,
                      'list': self._packer_multiple,
                      'tuple': self._packer_multiple,
                      'datetime': self._packer_datetime,
                     }

        for pattern in pack_patterns:

            perm_tokens = re.findall(_RE_PERMALINK, pattern.strip('/') + '/')
            base_permalist = [base_url] + perm_tokens

            # only the last token is allowed to be enclosed in '{}'
            for token in base_permalist[:-1]:
                if '{%s}' % token[1:-1] == token:
                    raise PermalinkTemplateError("Pack pattern %s has non-last "
                            "curly braces-enclosed field " % pattern)

            # determine which packer to use based on field type
            last_token = base_permalist[-1]
            field = last_token[1:-1]
            if '{%s}' % field != last_token:
                field_type = 'all'
            else:
                sample = getattr(units[0], field.split(':')[0])
                field_type = sample.__class__.__name__

            try:
                packer = packer_map[field_type]
                args = [field, base_permalist, units_per_pagination]
                pack_list = [pack for pack in packer(*args)]
                packs.extend(pack_list)
            except KeyError:
                raise NotImplementedError("Packer method for '%s' has not "
                                          "been implemented." % field_type)

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
            template_env - Jinja2 template environment.
            config_context - SessionConfig instance.

        """
        template_env = CONFIG.SITE.TEMPLATE_ENV
        template_file = os.path.basename(template_path)
        template = template_env.get_template(template_file)

        config_context = CONFIG

        for unit in self.units:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexpected results
            if os.path.exists(unit.path):
                raise DuplicateOutputError("'%s' already exists." % unit.path)
            try:
                os.makedirs(os.path.dirname(unit.path))
            except OSError:
                pass
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, \
                        CONFIG=config_context)
                self.write_output(target, rendered)

    def write_packs(self, template_path):
        """Writes packs into the given output file.

        Args:
            template_path - Template file name, must exist in the defined template
                directory.
            template_env - Jinja2 template environment.
            config_context - SessionConfig instance.

        """
        template_env = CONFIG.SITE.TEMPLATE_ENV
        template_file = os.path.basename(template_path)
        template = template_env.get_template(template_file)

        config_context = CONFIG

        for pack in self.packs:
            for pagination in pack.paginations:
                # warn if files are overwritten
                # this indicates a duplicate post, which could result in
                # unexpected results
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
                    rendered = template.render(page=pagination.__dict__, \
                            CONFIG=config_context)
                    self.write_output(target, rendered)

class Page(object):

    """Class representing resources that may have its own web page, such as
    a Unit or a Pagination instance."""

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.id)

    def slugify(self, string):
        """Returns a slugified version of the given string."""
        string = string.strip()

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, bad chars, and dashes in front and end
        string = re.sub(_RE_PRUNE, '', string)

        # raise exception if there are non-ascii chars
        try:
            if not sys.version_info[0] > 2:
                string.decode('ascii')
            else:
                assert all(ord(c) < 128 for c in string)
        except (UnicodeDecodeError, AssertionError):
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


class Unit(Page):

    """Base Volt Unit class.

    The unit class represent a single resource used for generating the site,
    such as a blog post, an image, or a regular plain text file.

    """

    def __init__(self, id):
        """Initializes a unit instance with the given ID string."""
        self.id = id

    @property
    def fields(self):
        """Returns the unit namespace."""
        return self.__dict__.keys()

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime
    get_display_time = datetime.strftime

    def parse_header(self, header_string):
        """Parses the YAML header string into a dictionary object.

        This is a thin wrapper for yaml.load, so it's more convenient
        for subclassing unit classes to parse YAML contents.

        """
        # why can't this be assigned directly like the other wrappers?
        return yaml.load(header_string)

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
            if '{%s}' % item[1:-1] == item:
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

    def set_paths(self, base_dir=None, abs_url=None, index_html_only=None):
        """Sets the permalink and absolute file path for the unit.

        Args:
            unit - Unit instance whose path and URL are to be set

        Keyword Args:
            base_dir - Absolute file system path to the output site directory
            abs_url - String of base absolute URL (e.g. http://foo.com)
            index_html_only -  Boolean indicating output file name;  if False
                then the output file name is '%s.html' where %s is the last
                string of the unit's permalist

        Output file defaults to 'index' so each unit will be written to
        'index.html' in its path. This allows for nice URLs without fiddling
        with .htaccess too much.

        """
        assert hasattr(self, 'permalist'), \
                "%s requires the 'permalist' attribute to be set first." % \
                self.__class__.__name__

        if abs_url is None:
            abs_url = CONFIG.SITE.URL
        if base_dir is None:
            base_dir = CONFIG.VOLT.SITE_DIR
        if index_html_only is None:
            index_html_only = CONFIG.SITE.INDEX_HTML_ONLY

        rel_url = ['']
        path = [base_dir]

        # set path and urls
        path.extend(self.permalist)
        rel_url.extend(filter(None, self.permalist))
        if index_html_only:
            rel_url[-1] = rel_url[-1] + '/'
            path.append('index.html')
        else:
            rel_url[-1] = rel_url[-1] + '.html'
            path[-1] = path[-1] + '.html'
        setattr(self, 'permalink', '/'.join(rel_url))
        setattr(self, 'permalink_abs', '/'.join([abs_url] + rel_url[1:]).strip('/'))
        setattr(self, 'path', os.path.join(*(path)))


class Pagination(Page):

    """Class representing a single paginated HTML file.

    The pagination class computes the necessary attributes required to write
    a single HTML file containing the desired units. It is the __dict__ object
    of this Pagination class that will be passed on to the template writing
    environment. However, the division of which units go to which pagination
    page is done by another class instantiating Pagination, for example the
    Pack class.

    """

    def __init__(self, units, pack_idx, base_permalist=[], title='',
            is_last=False, pagination_url=None, site_dir=None):
        """Initializes a Pagination instance.

        Args:
            units - List containing units to pack.
            pack_idx - Current pack object index.

        Keyword Args:
            title - String denoting the title of the pagination page.
            base_permalist - List of URL components common to all pack
                permalinks.
            is_last - Boolean indicating whether this pack is the last one.
            pagination_url - String denoting the URL token appended to
                paginations after the first one.
            site_dir - String denoting absolute path to site output directory.

        """
        self.title = title
        self.units = units
        # because page are 1-indexed and lists are 0-indexed
        self.pack_idx = pack_idx + 1
        # this will be appended for pack_idx > 1, e.g. .../page/2
        # precautions for empty string, so double '/'s are not introduced
        base_permalist = filter(None, base_permalist)

        index_html_only = CONFIG.SITE.INDEX_HTML_ONLY

        if pagination_url is None:
            pagination_url = CONFIG.SITE.PAGINATION_URL
        if site_dir is None:
            site_dir = CONFIG.VOLT.SITE_DIR

        if self.pack_idx == 1:
            # if it's the first pack page, use base_permalist only
            self.permalist = base_permalist
        else:
            # otherwise add pagination dir and pack index
            self.permalist = base_permalist + filter(None, [pagination_url, \
                    str(self.pack_idx)])

        # set path and url
        path = [site_dir]
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

        self.id = self.permalink

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        base_pagination_url = [''] + base_permalist
        # next permalinks
        if not is_last:
            self.permalink_next = '/'.join(base_pagination_url + filter(None, \
                    [pagination_url, str(self.pack_idx + 1)]))
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(base_pagination_url)
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(base_pagination_url + filter(None, \
                    [pagination_url, str(self.pack_idx - 1)]))

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

    def __init__(self, unit_matches, base_permalist, units_per_pagination):
        """Initializes a Pack object.

        Args:
            unit_matches - List of all units sharing a certain field value.
            base_permalist - Permalink tokens that will be used by all
                paginations of the given units.
            units_per_pagination - Number of units to show per pagination.

        Selection of the units to pass on to initialize Pack is done by an
        Engine object. An example of method that does this in the base Engine
        class is the build_packs method.

        """
        self.id = '/'.join(base_permalist)
        self.paginations = []

        # count how many paginations we need
        pagination = len(unit_matches) // units_per_pagination + \
                (len(unit_matches) % units_per_pagination != 0)

        # construct pagination objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pagination
            if i != pagination - 1:
                stop = (i + 1) * units_per_pagination
                self.paginations.append(Pagination(\
                        unit_matches[start:stop], i, \
                        base_permalist, title=''))
            else:
                self.paginations.append(Pagination(\
                        unit_matches[start:], i, \
                        base_permalist, title='', is_last=True))
