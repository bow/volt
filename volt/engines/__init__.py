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
from volt.engines.unit import TextUnit, _RE_PERMALINK


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
        self.packs = dict()
        self.config = Config(self.DEFAULTS)

    def prime(self):
        """Consolidates default engine Config and user-defined Config.

        In addition to consolidating Config values, this method also sets
        the values of CONTENT_DIR, and *_TEMPLATE to absolute directory paths.

        """
        if self.USER_CONF_ENTRY is None:
            raise NotImplementedError("Engine subclass must define a "
                                      "'USER_CONF_ENTRY' class attribute.")

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
        units = []
        targets = self.globdir(content_dir, is_gen=True)
        files = (x for x in targets if os.path.isfile(x))

        # parse each file and fill self.contents with TextUnit-s
        # also set its URL and absolute file path to be written
        for fname in files:
            units.append(TextUnit(fname, config))

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

    def build_packs(self, pack_patterns, base_url=None, \
            units_per_pagination=None, index_html_only=None):
        """Build packs of units and return them in a dictionary.

        Args:
            pack_patterns - List containing packs patterns to build.

        Keyword Args:
            base_url - String indicating base URL common to all paginations.
            units_per_pagination - Integer indicating how many units to include
                per pagination.
            index_html_only - Boolean indicating whether to print output HTML
                as index.html files or not.

        This method will expand the supplied pack_pattern according to
        the values present in all units. For example, if the pack_pattern
        is '{time:%Y}' and there are ten posts written with a 2010 year,
        build_pack will return a dictionary containing one entry with '2010'
        as the key and a Pack object containing the ten posts as the value.

        """
        # set shared options (which defaults to None for testing purposes)
        if base_url is None:
            base_url = self.config.URL.strip('/')

        if units_per_pagination is None:
            try:
                units_per_pagination = self.config.POSTS_PER_PAGE
            except AttributeError:
                raise ConfigError("%s Config must define a "
                                  "'POSTS_PER_PAGE' if build_packs() is "
                                  "used." % self.__class__.__name__)

        if index_html_only is None:
            index_html_only = CONFIG.SITE.INDEX_HTML_ONLY

        shared_pack_config = [base_url, units_per_pagination, index_html_only]

        # dictionary to contain all built packs
        packs = dict()
        # build_packs should operate on self.units
        units = self.units
        if not units:
            warnings.warn("%s has no units to pack.", EmptyUnitsWarning)

        for pack in pack_patterns:

            # get all tokens in the pack pattern
            base_permalist = re.findall(_RE_PERMALINK, pack.strip('/') + '/')

            # if token is not set, build pack for all units
            if base_permalist == []:
                unit_groups = [units]
                for units in unit_groups:
                    packs[''] = Pack(units, base_permalist, \
                            *shared_pack_config)

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
                        packs[key] = Pack(unit_groups, base_permalist, \
                                *shared_pack_config)

                # similar logic as before, but this time for string field values
                elif isinstance(getattr(units[0], field), basestring):
                    # get a set of all string values
                    all_items = set([getattr(x, field) for x in units])
                    for item in all_items:
                        unit_groups = [x for x in units if item == getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist, 
                                *shared_pack_config)

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
                        packs[key] = Pack(unit_groups, base_permalist, \
                                *shared_pack_config)

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
            is_last=False, index_html_only=True, pagination_url=None,
            site_dir=None):
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

    def __init__(self, unit_matches, base_permalist, base_url, \
            units_per_pagination, index_html_only):
        """Initializes a Pack object.

        Args:
            unit_matches - List of all units sharing a certain field value.
            base_permalist - Permalink tokens that will be used by all
                paginations of the given units.

        Keyword Args:
            base_url - String indicating base URL common to all paginations.
            units_per_pagination - Integer indicating how many units to include
                per pagination.
            index_html_only - Boolean indicating whether to print output HTML
                as index.html files or not.

        Selection of the units to pass on to initialize Pack is done by an
        Engine object. An example of method that does this in the base Engine
        class is the build_packs method.

        """
        # list to contain all paginations
        self.paginations = []

        # construct permalist tokens, relative to blog URL
        base_permalist = filter(None, [base_url] + base_permalist)

        # count how many paginations we need
        pagination = len(unit_matches) / units_per_pagination + \
                (len(unit_matches) % units_per_pagination != 0)

        # construct pagination bjects for each pagination page
        for i in range(pagination):
            start = i * units_per_pagination
            if i != pagination - 1:
                stop = (i + 1) * units_per_pagination
                self.paginations.append(Pagination(\
                        unit_matches[start:stop], i, \
                        base_permalist, title='', \
                        index_html_only=index_html_only))
            else:
                self.paginations.append(Pagination(\
                        unit_matches[start:], i, \
                        base_permalist, title='', is_last=True, \
                        index_html_only=index_html_only))
