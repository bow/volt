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
import codecs
import os
import re
import sys
import warnings
from datetime import datetime
from functools import partial, reduce

from volt.config import CONFIG, Config
from volt.exceptions import *
from volt.utils import path_import


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
    try:
        for idx, item in enumerate(items):
            if idx != 0:
                setattr(item, 'permalink_prev', items[idx-1].permalink)
            if idx != len(items) - 1:
                setattr(item, 'permalink_next', items[idx+1].permalink)
    except AttributeError:
        raise ContentError("%s '%s' neighbor(s) does not have a "
                           "permalink attribute." % \
                           (item.__class__.__name__.capitalize(), item.id))


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

    DEFAULTS = Config()

    def __init__(self):
        self.units = list()
        self.paginations = dict()
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

    def create_units(self):
        """Creates the units that will be processed by the engine."""
        raise NotImplementedError("%s must implement a create_units method." % \
                self.__class__.__name__)

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
                paginate_list = [pagination.next() for pagination in paginate(*args)]
                key = '/'.join(base_permalist)
                paginations[key] = paginate_list
            except KeyError:
                raise NotImplementedError("Pagination method for '%s' has not "
                                          "been implemented." % field_type)

        return paginations

    def _paginate_all(self, field, base_permalist, units_per_pagination):
        """Create paginations for all field values (PRIVATE)."""
        yield self._paginator(self.units, base_permalist, units_per_pagination)

    def _paginate_single(self, field, base_permalist, units_per_pagination):
        """Create paginations for string/int/float header field values (PRIVATE)."""
        units = self.units
        str_set = set([getattr(x, field) for x in units])

        for item in str_set:
            matches = [x for x in units if item == getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            yield self._paginator(matches, base_permalist, units_per_pagination)

    def _paginate_multiple(self, field, base_permalist, units_per_pagination):
        """Create paginations for list or tuple header field values (PRIVATE)."""
        units = self.units
        item_list_per_unit = (getattr(x, field) for x in units)
        item_set = reduce(set.union, [set(x) for x in item_list_per_unit])

        for item in item_set:
            matches = [x for x in units if item in getattr(x, field)]
            base_permalist = base_permalist[:-1] + [str(item)]
            yield self._paginator(matches, base_permalist, units_per_pagination)

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
            yield self._paginator(matches, base_permalist, units_per_pagination)

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

        for pagination in paginations:
            yield pagination

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
        config_context = CONFIG

        for item in items:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexpected results
            if os.path.exists(item.path):
                raise DuplicateOutputError("'%s' already exists." % item.path)
            try:
                os.makedirs(os.path.dirname(item.path))
            except OSError:
                pass
            with open(item.path, 'w') as target:
                rendered = template.render(page=item.__dict__, \
                        CONFIG=config_context)
                self._write_output(target, rendered)

    def _write_output(self, file_obj, string):
        """Writes string to the open file object."""
        if sys.version_info[0] < 3:
            string = string.encode('utf-8')
        file_obj.write(string)


class Page(object):

    """Class representing resources that may have its own web page, such as
    a Unit or a Pagination."""

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

    def get_path_and_permalink(self):
        """Returns the permalink and absolute file path."""
        assert hasattr(self, 'permalist'), \
                "%s requires the 'permalist' attribute to be set first." % \
                self.__class__.__name__

        abs_url = CONFIG.SITE.URL
        index_html_only = CONFIG.SITE.INDEX_HTML_ONLY
        base_path = [CONFIG.VOLT.SITE_DIR]
        rel_url = ['']

        permalist = self.permalist
        base_path.extend(permalist)
        rel_url.extend(filter(None, permalist))

        if index_html_only:
            rel_url[-1] = rel_url[-1] + '/'
            base_path.append('index.html')
        else:
            rel_url[-1] = rel_url[-1] + '.html'
            base_path[-1] = base_path[-1] + '.html'

        path = os.path.join(*base_path)
        permalink = '/'.join(rel_url)
        permalink_abs = '/'.join([abs_url] + rel_url[1:]).strip('/')

        return path, permalink, permalink_abs


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
        return self.__dict__.keys()

    # convenience methods
    open_text = partial(codecs.open, encoding='utf-8')
    as_datetime = datetime.strptime
    get_display_time = datetime.strftime

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

    def get_permalist(self, pattern, unit_base_url='/'):
        """Returns a list of strings which will be used to construct permalinks.

        pattern -- String replacement pattern.
        unit_base_url -- String of base URL of the engine, to be appended in
                         front of each unit URL.

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
        perm_tokens = re.findall(_RE_PERMALINK, pattern)

        # process components that are enclosed in {}
        permalist = []
        for token in perm_tokens:
            if '{%s}' % token[1:-1] == token:
                field = token[1:-1]
                if ':' in field:
                    field, fmt = field.split(':')
                if not hasattr(self, field):
                    raise PermalinkTemplateError("'%s' has no '%s' attribute." % \
                            (self.id, field))
                if isinstance(getattr(self, field), datetime):
                    strftime = datetime.strftime(getattr(self, field), fmt)
                    permalist.extend(filter(None, strftime.split('/')))
                else:
                    permalist.append(self.slugify(getattr(self, field)))
            else:
                permalist.append(self.slugify(token))

        return [unit_base_url.strip('/')] + filter(None, permalist)


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

        # set paths and permalist
        self.permalist = self.get_permalist()
        self.path, self.permalink, self.permalink_abs = self.get_path_and_permalink()
        self.id = self.permalink

    def get_permalist(self):
        """Returns a list of strings which will be used to construct permalinks."""
        pagination_url = CONFIG.SITE.PAGINATION_URL

        if self.pagin_idx == 1:
            # if it's the first pagination page, use base_permalist only
            permalist = self.base_permalist
        else:
            # otherwise add pagination dir and pagination index
            permalist = self.base_permalist + \
                    filter(None, [pagination_url, str(self.pagin_idx)])

        return permalist
