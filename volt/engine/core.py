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

from volt.config import CONFIG, Config
from volt.exceptions import *
from volt.utils import path_import, write_file


# regex objects for unit header and permalink processing
_RE_DELIM = re.compile(r'^---$', re.MULTILINE)
_RE_SPACES = re.compile(r'\s([A|a]n??)\s|_|\s+')
_RE_PRUNE = re.compile(r'A-|An-|[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]')
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


class Engine(object):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each unit. This base engine class does not perform any processing by
    itself, but provides convenient unit processing methods for the
    subclassing engine.

    Any subclass of Engine must override these methods:
    - activate
    - dispatch
    - create_units

    """

    __metaclass__ = abc.ABCMeta

    DEFAULTS = Config()

    def __init__(self):
        self.units = list()
        self.paginations = dict()
        self.config = Config(self.DEFAULTS)

    @abc.abstractmethod
    def activate(self):
        """Performs initial processing of resources into unit objects."""

    @abc.abstractmethod
    def dispatch(self):
        """Performs final processing after all plugins are run."""

    @abc.abstractmethod
    def create_units(self):
        """Creates the units that will be processed by the engine."""

    def prime(self):
        """Consolidates default engine Config and user-defined Config.

        In addition to consolidating Config values, this method also sets
        the values of CONTENT_DIR, and *_TEMPLATE to absolute directory paths.

        """
        # get user config object
        conf_name = os.path.splitext(os.path.basename(CONFIG.VOLT.USER_CONF))[0]
        voltconf = path_import(conf_name, CONFIG.VOLT.ROOT_DIR)
        try:
            user_config = getattr(voltconf, self.USER_CONF_ENTRY)
        except AttributeError:
            raise ConfigError("%s must define a 'USER_CONF_ENTRY' value as a "
                              "class attribute." % self.__class__.__name__)

        # to ensure proper Config consolidation
        if not isinstance(user_config, Config):
            raise TypeError("User Config object '%s' must be a Config instance." % \
                    self.USER_CONF_ENTRY)

        self.config.update(user_config)

        # set absolute directory paths
        try:
            self.config.CONTENT_DIR = os.path.join(CONFIG.VOLT.CONTENT_DIR, \
                    self.config.CONTENT_DIR)
        except AttributeError:
            raise ConfigError("%s must define a 'CONTENT_DIR' value in "
                              "DEFAULTS." % self.__class__.__name__)

        for template in [x for x in self.config.keys() if x.endswith('_TEMPLATE')]:
                self.config[template] = os.path.join(CONFIG.VOLT.TEMPLATE_DIR, \
                        self.config[template])

    def chain_units(self):
        """Sets the previous and next permalink attributes of each unit."""
        chain_item_permalinks(self.units)

    def sort_units(self):
        """Sorts a list of units according to the given header field name."""
        sort_key = self.config.SORT_KEY
        reversed = sort_key.startswith('-')
        sort_key = sort_key.strip('-')
        try:
            self.units.sort(key=lambda x: getattr(x, sort_key), reverse=reversed)
        except AttributeError:
            raise ContentError("Sorting key '%s' not present in all unit "
                               "header field." % sort_key)

    def create_paginations(self):
        """Returns paginations of engine units in a dictionary.

        This method will expand the supplied patterns according to the values
        present in all units. For example, if the pattern is '{time:%Y}' and
        there are five units with a datetime.year attribute 2010 and another
        five with 2011, create_paginations will return a dictionary with one key
        pointing to a list containing paginations for 'time/2010' and
        'time/2011'. The number of actual paginations vary, depending on how
        many units are in one pagination.

        """
        try:
            base_url = self.config.URL.strip('/')
        except AttributeError:
            raise ConfigError("%s Config must define a 'URL' value if "
                              "create_paginations is used." % \
                              self.__class__.__name__)
        try:
            units_per_pagination = self.config.UNITS_PER_PAGINATION
        except AttributeError:
            raise ConfigError("%s Config must define a 'UNITS_PER_PAGINATION' value "
                              "if create_paginations is used." % \
                              self.__class__.__name__)
        try:
            pagination_patterns = self.config.PAGINATIONS
        except AttributeError:
            raise ConfigError("%s Config must define a 'PAGINATIONS' value "
                              "if create_paginations is used." % \
                              self.__class__.__name__)

        # create_paginations operates on self.units
        units = self.units
        if not units:
            warnings.warn("%s has no units to paginate." % self.__class__.__name__, \
                    EmptyUnitsWarning)
            # exit function if there's no units to process
            return

        paginator_map = {
                'all': self._paginate_all,
                'str': self._paginate_single,
                'int': self._paginate_single,
                'float': self._paginate_single,
                'list': self._paginate_multiple,
                'tuple': self._paginate_multiple,
                'datetime': self._paginate_datetime,
        }

        paginations = dict()
        for pattern in pagination_patterns:

            perm_tokens = re.findall(_RE_PERMALINK, pattern.strip('/') + '/')
            base_permalist = [base_url] + perm_tokens

            # only the last token is allowed to be enclosed in '{}'
            for token in base_permalist[:-1]:
                if '{%s}' % token[1:-1] == token:
                    raise PermalinkTemplateError("Pagination pattern %s has "
                            "non-last curly braces-enclosed field " % pattern)

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
                args = [field, base_permalist, units_per_pagination]
                paginate_list = list(paginate(*args))
                key = '/'.join(base_permalist)
                paginations[key] = paginate_list
            except KeyError:
                raise NotImplementedError("Pagination method for '%s' has not "
                                          "been implemented." % field_type)

        return paginations

    def _paginate_all(self, field, base_permalist, units_per_pagination):
        """Create paginations for all field values (PRIVATE)."""
        return self._paginator(self.units, base_permalist, units_per_pagination)

    def _paginate_single(self, field, base_permalist, units_per_pagination):
        """Create paginations for string/int/float header field values (PRIVATE)."""
        units = self.units
        str_set = set([getattr(x, field) for x in units])

        paginated = list()
        for item in str_set:
            matches = [x for x in units if item == getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            pagin = self._paginator(matches, base_permalist, units_per_pagination)
            paginated.extend(pagin)

        return paginated

    def _paginate_multiple(self, field, base_permalist, units_per_pagination):
        """Create paginations for list or tuple header field values (PRIVATE)."""
        units = self.units
        item_list_per_unit = (getattr(x, field) for x in units)
        item_set = reduce(set.union, [set(x) for x in item_list_per_unit])

        paginated = list()
        for item in item_set:
            matches = [x for x in units if item in getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            pagin = self._paginator(matches, base_permalist, units_per_pagination)
            paginated.extend(pagin)

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

        paginated = list()
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

        return paginated

    def _paginator(self, units, base_permalist, units_per_pagination):
        """Create paginations from units (PRIVATE).

        units -- List of all units which will be paginated.
        base_permalist -- List of permalink tokens that will be used by all
                          paginations of the given units.
        units_per_pagination -- Number of units to show per pagination.

        """
        paginations = list()

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

        chain_item_permalinks(paginations)

        return paginations

    def write_units(self):
        """Writes units using the unit template file."""
        self._write_items(self.units, self.config.UNIT_TEMPLATE)

    def write_paginations(self):
        """Writes paginations using the pagination template file."""
        for pagination in self.paginations.values():
            self._write_items(pagination, self.config.PAGINATION_TEMPLATE)

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
                raise DuplicateOutputError("'%s' already exists." % item.path)
            rendered = template.render(page=item, CONFIG=CONFIG)
            if sys.version_info[0] < 3:
                rendered = rendered.encode('utf-8')
            write_file(item.path, rendered)


class Page(object):

    """Class representing resources that may have its own web page, such as
    a Unit or a Pagination."""

    __metaclass__ = abc.ABCMeta

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.id)

    @abc.abstractproperty
    def permalist(self):
        """List of tokens used to construct permalink and path."""

    @abc.abstractproperty
    def id(self):
        """Unique string that identifies the Page object."""

    @property
    def path(self):
        """Filesystem path to Page object file."""
        if not hasattr(self, '_path'):
            base_path = [CONFIG.VOLT.SITE_DIR]
            base_path.extend(self.permalist)

            if CONFIG.SITE.INDEX_HTML_ONLY:
                base_path.append('index.html')
            else:
                base_path[-1] += '.html'

            self._path = os.path.join(*base_path)

        return self._path

    @property
    def permalink(self):
        """Relative URL to the Page object."""
        if not hasattr(self, '_permalink'):
            rel_url = ['']
            rel_url.extend(filter(None, self.permalist))

            if CONFIG.SITE.INDEX_HTML_ONLY:
                rel_url[-1] += '/'
            else:
                rel_url[-1] += '.html'

            self._permalink = '/'.join(rel_url)

        return self._permalink

    @property
    def permalink_abs(self):
        """Absolute URL to the Page object."""
        if not hasattr(self, '_permalink_abs'):
            self._permalink_abs = '/'.join([CONFIG.SITE.URL, \
                    self.permalink[1:]]).strip('/')

        return self._permalink_abs

    def slugify(self, string):
        """Returns a slugified version of the given string."""
        string = string.strip()

        # replace spaces, etc with dash
        string = re.sub(_RE_SPACES, '-', string)

        # remove english articles, bad chars, and dashes in front and end
        string = re.sub(_RE_PRUNE, '', string)

        # raise exception if there are non-ascii chars
        try:
            if sys.version_info[0] > 2:
                assert all(ord(c) < 128 for c in string)
            else:
                string.decode('ascii')
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
            raise TypeError("Units must be instantiated with their engine's "
                            "Config object.")
        self.config = config

    @property
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
        if not hasattr(self, '_permalist'):
            try:
                # strip preceeding '/' but make sure ends with '/'
                pattern = self.config.PERMALINK.strip('/') + '/'
            except AttributeError:
                raise ConfigError("%s Config must define a 'PERMALINK' value."
                                  % self.__class__.__name__)
            try:
                unit_base_url = self.config.URL
            except AttributeError:
                raise ConfigError("%s Config must define a 'URL' value."
                                  % self.__class__.__name__)


            # get all permalink components and store into list
            perm_tokens = re.findall(_RE_PERMALINK, pattern)

            # process components that are enclosed in {}
            permalist = []
            for token in perm_tokens:
                if '{%s}' % token[1:-1] == token:
                    field = token[1:-1]
                    if ':' in field:
                        field, fmt = field.split(':')
                    if not hasattr(self, field):
                        raise PermalinkTemplateError("'%s' has no '%s' "
                            "attribute." % (self.id, field))
                    if isinstance(getattr(self, field), datetime):
                        strftime = datetime.strftime(getattr(self, field), fmt)
                        permalist.extend(filter(None, strftime.split('/')))
                    else:
                        permalist.append(self.slugify(getattr(self, field)))
                else:
                    permalist.append(self.slugify(token))

            self._permalist = [unit_base_url.strip('/')] + \
                    filter(None, permalist)

        return self._permalist

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime

    def check_protected(self, field, prot):
        """Checks if the given field can be set by the user or not.
        
        field -- String to check against the list containing protected fields.
        prot -- Iterable returning string of protected fields.

        """
        if field in prot:
            raise ContentError("'%s' should not define the protected header "
                               "field '%s'" % (self.id, field))

    def check_required(self, req):
        """Checks if all the required header fields are present.

        req -- Iterable returning string of required header fields.

        """
        for field in req:
            if not hasattr(self, field):
                raise ContentError("Required header field '%s' is missing in "
                                   "'%s'." % (field, self.id))

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

    @property
    def id(self):
        return self.permalink

    @property
    def permalist(self):
        """Returns a list of strings which will be used to construct permalinks."""
        if not hasattr(self, '_permalist'):
            self._permalist = self.base_permalist
            # add pagination url and index if it's not the first pagination page
            if self.pagin_idx > 1:
                self._permalist += filter(None, [CONFIG.SITE.PAGINATION_URL, \
                        str(self.pagin_idx)])

        return self._permalist
