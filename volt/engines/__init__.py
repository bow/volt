# -*- coding: utf-8 -*-
"""
-----------
volt.engine
-----------

Base Engine, Pack, and Pagination classes.

Engines are classes that perform initial processing of Unit objects
(see volt.engine.unit). Packs represent a collection of Units sharing similar
attributes. Paginations are groups of several Units that will be written to a
single HTML file, for example blog posts written in February 2009.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import glob
import os
import re
import warnings

from volt.config import CONFIG, Config, ConfigError, path_import
from volt.engines.unit import \
        _RE_PERMALINK, TextUnit, Pack, HeaderFieldError, ContentError, \
        PermalinkTemplateError


class DuplicateOutputError(Exception):
    """Raised when Volt tries to overwrite an existing HTML output file.

    This is an exception because in a normal Volt run, there should be no
    duplicate output file. Each unit and pack should have its own unique
    absolute path.

    """
    pass

class EmptyUnitsWarning(RuntimeWarning):
    """Issued when build_packs is called without any units to pack in self.units."""


class Engine(object):

    """Base Volt Engine class.

    Engine is the core component of Volt that performs initial processing
    of each unit. This base engine class does not perform any processing by
    itself, but provides convenient unit processing methods for the
    subclassing engine.

    Subclassing classes must override the ``parse`` and ``write`` methods
    of the base engine class.

    """

    DEFAULTS = Config()

    USER_CONF_ENTRY = None

    def __init__(self):
        """Initializes the engine."""
        self.units = list()
        self.packs = list()
        self.config = Config(self.DEFAULTS)

    def prime(self):
        """Consolidates default engine Config and user-defined Config.

        In addition to consolidating Config values, this method also sets
        the values of CONTENT_DIR, and *_TEMPLATE to absolute directory paths.

        """
        if self.USER_CONF_ENTRY is None:
            raise NotImplementedError("Engine subclass must define a "
                                      "'USER_CONF_ENTRY' class attribute.")

        if not hasattr(self.config, 'CONTENT_DIR'):
            raise ConfigError("Engine subclass must define a 'CONTENT_DIR' "
                              "value in DEFAULTS.")

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

    def process_text_units(self, config, content_dir):
        """Processes units into a TextUnit object and returns them in a list.

        Args:
            config - Config object corresponding to the engine settings,
                e.g. config.BLOG for the BlogEngine or config.PLAIN
                for the PlainEngine.
            content_dir - Absolute path to directory containing text files
                to process.

        """
        # get absolute paths of content files
        targets = glob.iglob(os.path.join(content_dir, '*'))
        files = (x for x in targets if os.path.isfile(x))
        units = [TextUnit(fname, config) for fname in files]

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
        try:
            units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)
        except AttributeError:
            raise HeaderFieldError("Sorting key '%s' not present in all unit "
                                   "header field." % sort_key)

    def chain_units(self, units):
        """Sets the previous and next permalink attributes of units in a list.

        Args:
            units - List containing units to chain

        This method allows each unit in a list to link to its previous and/or
        next unit according to the ordering in the list.

        """
        try:
            for idx, unit in enumerate(units):
                if idx != 0:
                    setattr(unit, 'permalink_prev', units[idx-1].permalink)
                if idx != len(units) - 1:
                    setattr(unit, 'permalink_next', units[idx+1].permalink)
            return units
        except AttributeError:
            raise ContentError("Unit '%s' neighbor(s) does not have a "
                               "permalink attribute." % unit.id)

    def _packer_all(self, field, base_permalist, units_per_pagination):
        """Build packs for all field values (PRIVATE)."""
        units = self.units
        yield Pack(units, base_permalist, units_per_pagination)

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
        """Build packs of units and return them in a dictionary.

        Args:
            pack_patterns - List containing packs patterns to build.

        This method will expand the supplied pack_pattern according to
        the values present in all units. For example, if the pack_pattern
        is '{time:%Y}' and there are ten posts written with a 2010 year,
        build_pack will return a dictionary containing one entry with '2010'
        as the key and a Pack object containing the ten posts as the value.

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

    def write_units(self, template_path, template_env=None, config_context=None):
        """Writes single units into the given output file.

        Args:
            template_path - Template file name, must exist in the defined template
                directory.
            template_env - Jinja2 template environment.
            config_context - SessionConfig instance.

        """
        if template_env is None:
            template_env = CONFIG.SITE.TEMPLATE_ENV
        template_file = os.path.basename(template_path)
        template = template_env.get_template(template_file)

        if config_context is None:
            config_context = CONFIG

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
                rendered = template.render(page=unit.__dict__, \
                        CONFIG=config_context)
                self.write_output(target, rendered)

    def write_packs(self, template_path, template_env=None, config_context=None):
        """Writes packs into the given output file.

        Args:
            template_path - Template file name, must exist in the defined template
                directory.
            template_env - Jinja2 template environment.
            config_context - SessionConfig instance.

        """
        if template_env is None:
            template_env = CONFIG.SITE.TEMPLATE_ENV
        template_file = os.path.basename(template_path)
        template = template_env.get_template(template_file)

        if config_context is None:
            config_context = CONFIG

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
                    rendered = template.render(page=pagination.__dict__, \
                            CONFIG=config_context)
                    self.write_output(target, rendered)

    def activate(self):
        """Performs initial processing of resources into unit objects."""
        raise NotImplementedError("Engine subclass must implement an activate method.")

    def dispatch(self):
        """Performs final processing after all plugins are run."""
        raise NotImplementedError("Engine subclass must implement a dispatch method.")
