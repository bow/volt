# -*- coding: utf-8 -*-
"""
----------------
volt.engine.core
----------------

Volt core engine classes.

Contains the Engine, Page, Unit, and Pagination classes.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import abc
import codecs
import os
import re
import sys
import warnings
from datetime import datetime
from functools import partial, reduce
from traceback import format_exc

from volt.config import CONFIG, Config
from volt.exceptions import EmptyUnitsWarning
from volt.utils import LoggableMixin, cachedproperty, path_import, write_file


# required engine config values
_REQUIRED_ENGINE_CONFIG = ('URL', 'CONTENT_DIR', 'PERMALINK',)

# required engine config for paginations
_REQUIRED_ENGINE_PAGINATIONS = ('PAGINATIONS', 'UNITS_PER_PAGINATION',)

# regex objects for unit header and permalink processing
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[^a-zA-Z0-9_-]')
_RE_MULTIPLE = re.compile(r'-+')
_RE_PERMALINK = re.compile(r'(.+?)/+(?!%)')


# chain item permalinks, for Engine.units and Engine.paginations
def chain_item_permalinks(items):
    """Sets the previous and next permalink attributes of items.

    items -- List containing item to chain.

    This method sets a 'permalink_prev' and 'permalink_next' attribute
    for each item in the given list, which are permalinks to the previous
    and next items.

    """
    for idx, item in enumerate(items):
        if idx != 0:
            setattr(item, 'permalink_prev', items[idx-1].permalink)
        if idx != len(items) - 1:
            setattr(item, 'permalink_next', items[idx+1].permalink)


class Engine(LoggableMixin):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each unit. This base engine class does not perform any processing by
    itself, but provides convenient unit processing methods for the
    subclassing engine.

    Any subclass of Engine must create a 'units' property and override the
    dispatch method. Optionally, the preprocess method may be overridden if any
    unit processing prior to plugin run needs to be performed.

    """

    __metaclass__ = abc.ABCMeta

    DEFAULTS = Config()

    def __init__(self):
        self.config = Config(self.DEFAULTS)
        self.logger.debug('created: %s' % type(self).__name__)
        # attributes below are placeholders for template access later on
        self.widgets = {}

    def preprocess(self):
        """Performs initial processing of units before plugins are run."""
        pass

    @abc.abstractmethod
    def dispatch(self):
        """Performs final processing after all plugins are run."""

    @abc.abstractmethod
    def units(self):
        """Units of the engine."""

    def prime(self):
        """Consolidates default engine Config and user-defined Config.

        In addition to consolidating Config values, this method also sets
        the values of CONTENT_DIR, and *_TEMPLATE to absolute directory paths.

        """
        # get user config object
        conf_name = os.path.splitext(os.path.basename(CONFIG.VOLT.USER_CONF))[0]
        user_conf = path_import(conf_name, CONFIG.VOLT.ROOT_DIR)

        # custom engines must define an entry name for the user's voltconf
        if not hasattr (self, 'USER_CONF_ENTRY'):
            message = "%s must define a %s value as a class attribute." % \
                    (type(self).__name__, 'USER_CONF_ENTRY')
            self.logger.error(message)

        # use default config if the user does not specify any
        try:
            user_config = getattr(user_conf, self.USER_CONF_ENTRY)
        except AttributeError:
            user_config = Config()

        # to ensure proper Config consolidation
        if not isinstance(user_config, Config):
            message = "User Config object '%s' must be a Config instance." % \
                    self.USER_CONF_ENTRY
            self.logger.error(message)
            raise TypeError(message)
        else:
            self.config.update(user_config)

        # check attributes that must exist
        for attr in _REQUIRED_ENGINE_CONFIG:
            try:
                getattr(self.config, attr)
            except AttributeError:
                message = "%s Config '%s' value is undefined." % \
                        (type(self).__name__, attr)
                self.logger.error(message)
                self.logger.debug(format_exc())
                raise

        # set engine config paths to absolute paths
        self.config.CONTENT_DIR = os.path.join(CONFIG.VOLT.CONTENT_DIR, \
                self.config.CONTENT_DIR)
        for template in [x for x in self.config.keys() if x.endswith('_TEMPLATE')]:
                self.config[template] = os.path.join(CONFIG.VOLT.TEMPLATE_DIR, \
                        self.config[template])

    def chain_units(self):
        """Sets the previous and next permalink attributes of each unit."""
        chain_item_permalinks(self.units)
        self.logger.debug('done: chaining units')

    def sort_units(self):
        """Sorts a list of units according to the given header field name."""
        sort_key = self.config.SORT_KEY
        reversed = sort_key.startswith('-')
        sort_key = sort_key.strip('-')
        try:
            self.units.sort(key=lambda x: getattr(x, sort_key), reverse=reversed)
        except AttributeError:
            message = "Sort key '%s' not present in all units." % sort_key
            self.logger.error(message)
            self.logger.debug(format_exc())
            raise

        self.logger.debug("done: sorting units based on '%s'" % self.config.SORT_KEY)

    @cachedproperty
    def paginations(self):
        """Paginations of engine units in a dictionary.

        The computation will expand the supplied patterns according to the values
        present in all units. For example, if the pattern is '{time:%Y}' and
        there are five units with a datetime.year attribute 2010 and another
        five with 2011, create_paginations will return a dictionary with one key
        pointing to a list containing paginations for 'time/2010' and
        'time/2011'. The number of actual paginations vary, depending on how
        many units are in one pagination.

        """
        # check attributes that must exist
        for attr in _REQUIRED_ENGINE_PAGINATIONS:
            try:
                getattr(self.config, attr)
            except AttributeError:
                message = "%s Config '%s' value is undefined." % \
                        (type(self).__name__, attr)
                self.logger.error(message)
                self.logger.debug(format_exc())
                raise

        base_url = self.config.URL.strip('/')
        units_per_pagination = self.config.UNITS_PER_PAGINATION
        pagination_patterns = self.config.PAGINATIONS

        # create_paginations operates on self.units
        units = self.units
        if not units:
            warnings.warn("%s has no units to paginate." % type(self).__name__, \
                    EmptyUnitsWarning)
            # exit function if there's no units to process
            return {}

        paginator_map = {
                'all': self._paginate_all,
                'str': self._paginate_single,
                'int': self._paginate_single,
                'float': self._paginate_single,
                'list': self._paginate_multiple,
                'tuple': self._paginate_multiple,
                'datetime': self._paginate_datetime,
        }

        paginations = {}
        for pattern in pagination_patterns:

            perm_tokens = re.findall(_RE_PERMALINK, pattern.strip('/') + '/')
            base_permalist = [base_url] + perm_tokens

            # only the last token is allowed to be enclosed in '{}'
            for token in base_permalist[:-1]:
                if '{%s}' % token[1:-1] == token:
                    message = "Pagination pattern %s is invalid." % pattern
                    self.logger.error(message)
                    raise ValueError(message)

            # determine which paginate method to use based on field type
            last_token = base_permalist[-1]
            field = last_token[1:-1]
            if '{%s}' % field != last_token:
                field_type = 'all'
            else:
                sample = getattr(units[0], field.split(':')[0])
                field_type = sample.__class__.__name__

            try:
                paginate = paginator_map[field_type]
            except KeyError:
                message = "Pagination method for '%s' has not been " \
                          "implemented." % field_type
                self.logger.error(message)
                self.logger.debug(format_exc())
                raise
            else:
                args = [field, base_permalist, units_per_pagination]
                paginate_list = list(paginate(*args))
                key = '/'.join(base_permalist)
                paginations[key] = paginate_list

        return paginations

    def _paginate_all(self, field, base_permalist, units_per_pagination):
        """Create paginations for all field values (PRIVATE)."""
        paginated = self._paginator(self.units, base_permalist, units_per_pagination)

        self.logger.debug('created: %d %s paginations' % (len(paginated), 'all'))
        return paginated

    def _paginate_single(self, field, base_permalist, units_per_pagination):
        """Create paginations for string/int/float header field values (PRIVATE)."""
        units = self.units
        str_set = set([getattr(x, field) for x in units])

        paginated = []
        for item in str_set:
            matches = [x for x in units if item == getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            pagin = self._paginator(matches, base_permalist, units_per_pagination)
            paginated.extend(pagin)

        self.logger.debug('created: %d %s paginations' % (len(paginated), field))
        return paginated

    def _paginate_multiple(self, field, base_permalist, units_per_pagination):
        """Create paginations for list or tuple header field values (PRIVATE)."""
        units = self.units
        item_list_per_unit = (getattr(x, field) for x in units)
        item_set = reduce(set.union, [set(x) for x in item_list_per_unit])

        paginated = []
        for item in item_set:
            matches = [x for x in units if item in getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            pagin = self._paginator(matches, base_permalist, units_per_pagination)
            paginated.extend(pagin)

        self.logger.debug('created: %d %s paginations' % (len(paginated), field))
        return paginated

    def _paginate_datetime(self, field, base_permalist, units_per_pagination):
        """Create paginations for datetime header field values (PRIVATE)."""
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

        paginated = []
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
            pagin = self._paginator(matches, base_permalist, units_per_pagination)
            paginated.extend(pagin)

        self.logger.debug('created: %d %s paginations' % (len(paginated), field))
        return paginated

    def _paginator(self, units, base_permalist, units_per_pagination):
        """Create paginations from units (PRIVATE).

        units -- List of all units which will be paginated.
        base_permalist -- List of permalink tokens that will be used by all
                          paginations of the given units.
        units_per_pagination -- Number of units to show per pagination.

        """
        paginations = []

        # count how many paginations we need
        is_last = len(units) % units_per_pagination != 0
        pagination_len = len(units) // units_per_pagination + int(is_last)

        # construct pagination objects for each pagination page
        for idx in range(pagination_len):
            start = idx * units_per_pagination
            if idx != pagination_len - 1:
                stop = (idx + 1) * units_per_pagination
                units_in_pagination = units[start:stop]
            else:
                units_in_pagination = units[start:]

            pagination = Pagination(units_in_pagination, idx, base_permalist)
            paginations.append(pagination)

        if len(paginations) > 1:
            chain_item_permalinks(paginations)
            self.logger.debug('done: chaining paginations')

        return paginations

    def write_units(self):
        """Writes units using the unit template file."""
        self._write_items(self.units, self.config.UNIT_TEMPLATE)
        self.logger.debug('written: %d %s unit(s)' % (len(self.units), \
                type(self).__name__[:-len('Engine')]))

    def write_paginations(self):
        """Writes paginations using the pagination template file."""
        for pattern in self.paginations:
            self._write_items(self.paginations[pattern], self.config.PAGINATION_TEMPLATE)
            self.logger.debug("written: '%s' pagination(s)" % pattern)

    def _write_items(self, items, template_path):
        """Writes Page objects using the given template file (PRIVATE).

        items -- List of Page objects to be written.
        template_path -- Template file name, must exist in the defined
                         template directory.

        """
        template_env = CONFIG.SITE.TEMPLATE_ENV
        template_file = os.path.basename(template_path)
        template = template_env.get_template(template_file)

        for item in items:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexpected results
            if os.path.exists(item.path):
                message = "File %s already exists. Make sure there are no "\
                          "other entries leading to this file path." % item.path
                self.logger.error(message)
                raise IOError(message)
            else:
                rendered = template.render(page=item, CONFIG=CONFIG, \
                        widgets=self.widgets)
                if sys.version_info[0] < 3:
                    rendered = rendered.encode('utf-8')
                write_file(item.path, rendered)


class Page(LoggableMixin):

    """Class representing resources that may have its own web page, such as
    a Unit or a Pagination."""

    __metaclass__ = abc.ABCMeta

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self.id)

    @abc.abstractproperty
    def permalist(self):
        """List of tokens used to construct permalink and path."""

    @abc.abstractproperty
    def id(self):
        """Unique string that identifies the Page object."""

    @cachedproperty
    def path(self):
        """Filesystem path to Page object file."""
        base_path = [CONFIG.VOLT.SITE_DIR]
        base_path.extend(self.permalist)

        if CONFIG.SITE.INDEX_HTML_ONLY:
            base_path.append('index.html')
        else:
            base_path[-1] += '.html'

        return os.path.join(*base_path)

    @cachedproperty
    def permalink(self):
        """Relative URL to the Page object."""
        rel_url = ['']
        rel_url.extend(filter(None, self.permalist))

        if CONFIG.SITE.INDEX_HTML_ONLY:
            rel_url[-1] += '/'
        else:
            rel_url[-1] += '.html'

        return '/'.join(rel_url)

    @cachedproperty
    def permalink_abs(self):
        """Absolute URL to the Page object."""
        return '/'.join([CONFIG.SITE.URL, self.permalink[1:]]).strip('/')

    def slugify(self, string):
        """Returns a slugified version of the given string."""
        string = string.strip()

        # perform user-defined character mapping
        for target in CONFIG.SITE.SLUG_CHAR_MAP:
            string = string.replace(target, CONFIG.SITE.SLUG_CHAR_MAP[target])

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, and non-ascii characters
        string = re.sub(_RE_PRUNE, '', string)

        # slug should not begin or end with dash or contain multiple dashes
        string = re.sub(_RE_MULTIPLE, '-', string)

        # and finally, we string preceeding and succeeding dashes
        string = string.lower().strip('-')

        # error if slug is empty
        if not string:
            message = "Slug for '%s' is an empty string." % self.id
            self.logger.error(message)
            raise ValueError(message)

        return string


class Unit(Page):

    """Base Volt Unit class.

    The unit class represent a single resource used for generating the site,
    such as a blog post, an image, or a regular plain text file.

    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        """Initializes a unit instance.

        id -- Unique string to identify the unit.
        config -- Config object of the calling Engine.

        Config objects are required to instantiate the Unit since some unit
        configuration values depends on the calling Engine configuration
        values.

        """
        if not isinstance(config, Config):
            message = "Units must be instantiated with their engine's " \
                    "Config object."
            self.logger.error(message)
            raise TypeError(message)
        self.config = config

    @cachedproperty
    def permalist(self):
        """Returns a list of strings which will be used to construct permalinks.

        For the permalist to be constructed, the calling Engine must define a
        'PERMALINK' string in its Config object.

        The permalink string pattern may refer to the current unit's attributes
        by enclosing them in square brackets. If the referred instance attribute
        is a datetime object, it must be formatted by specifying a string format
        argument.

        Several examples of a valid permalink pattern:

        '{time:%Y/%m/%d}/{slug}'
            Returns, for example, ['2009', '10', '04', 'the-slug']

        'post/{time:%d}/{id}'
            Returns, for example,  ['post', '04', 'item-103']

        """
        # strip preceeding '/' but make sure ends with '/'
        pattern = self.config.PERMALINK.strip('/') + '/'
        unit_base_url = self.config.URL

        # get all permalink components and store into list
        perm_tokens = re.findall(_RE_PERMALINK, pattern)

        # process components that are enclosed in {}
        permalist = []
        for token in perm_tokens:
            if '{%s}' % token[1:-1] == token:
                field = token[1:-1]
                if ':' in field:
                    field, fmt = field.split(':')

                try:
                    attr = getattr(self, field)
                except AttributeError:
                    message = "'%s' has no '%s' attribute." % (self.id, field)
                    self.logger.error(message)
                    self.logger.debug(format_exc())
                    raise

                if isinstance(attr, datetime):
                    strftime = datetime.strftime(attr, fmt)
                    permalist.extend(filter(None, strftime.split('/')))
                else:
                    permalist.append(self.slugify(attr))
            else:
                permalist.append(self.slugify(token))

        return [unit_base_url.strip('/')] + filter(None, permalist)

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime

    def parse_header(self, header_string):
        """Returns a dictionary of header field values.

        header_string -- String of header lines.

        """
        header_lines = [x.strip() for x in header_string.strip().split('\n')]
        for line in header_lines:
            if not ':' in line:
                    raise ValueError("Line '%s' in '%s' is not a proper "
                            "header entry." % (line, self.id))
            field, value = [x.strip() for x in line.split(':', 1)]

            self.check_protected(field, self.config.PROTECTED)

            if field == 'slug':
                value = self.slugify(value)

            elif field in self.config.FIELDS_AS_LIST:
                value = self.as_list(value, self.config.LIST_SEP)

            elif field in self.config.FIELDS_AS_DATETIME:
                value = self.as_datetime(value, \
                        self.config.DATETIME_FORMAT)

            setattr(self, field.lower(), value)

    def check_protected(self, field, prot):
        """Checks if the given field can be set by the user or not.
        
        field -- String to check against the list containing protected fields.
        prot -- Iterable returning string of protected fields.

        """
        if field in prot:
            message = "'%s' should not define the protected header field " \
                    "'%s'" % (self.id, field)
            self.logger.error(message)
            raise ValueError(message)

    def check_required(self, req):
        """Checks if all the required header fields are present.

        req -- Iterable returning string of required header fields.

        """
        for field in req:
            if not hasattr(self, field):
                message = "Required header field '%s' is missing in '%s'." % \
                        (field, self.id)
                self.logger.error(message)
                raise NameError(message)

    def as_list(self, field, sep):
        """Transforms a character-separated string field into a list.

        fields -- String to transform into list.
        sep -- String used to split fields into list.

        """
        return list(set(filter(None, field.strip().split(sep))))


class Pagination(Page):

    """Class representing a single paginated HTML file.

    The pagination class computes the necessary attributes required to write
    a single HTML file containing the desired units. It is the __dict__ object
    of this Pagination class that will be passed on to the template writing
    environment. The division of which units go to which pagination
    page is done by another method.

    """

    def __init__(self, units, pagin_idx, base_permalist=[], title=''):
        """Initializes a Pagination instance.

        units -- List containing units to paginate.
        pagin_idx -- Number of current pagination object index.
        base_permalist -- List of URL components common to all pagination
                          permalinks.
        title -- String denoting the title of the pagination page.

        """
        self.units = units
        self.title = title

        # since paginations are 1-indexed
        self.pagin_idx = pagin_idx + 1
        # precautions for empty string, so double '/'s are not introduced
        self.base_permalist = filter(None, base_permalist)
        self.logger.debug('created: %s' % self.id)

    @cachedproperty
    def id(self):
        return self.permalink

    @cachedproperty
    def permalist(self):
        """Returns a list of strings which will be used to construct permalinks."""
        permalist = self.base_permalist
        # add pagination url and index if it's not the first pagination page
        if self.pagin_idx > 1:
            permalist += filter(None, [CONFIG.SITE.PAGINATION_URL, \
                    str(self.pagin_idx)])

        return permalist
