# -*- coding: utf-8 -*-
"""
-----------
volt.config
-----------

Volt configuration container module.

This module provides classes for handling configurations used in a Volt site
generation. These configurations are obtained from two files: 1) the 
default_conf.py file in this module containining all default configurations
values, and 2) the voltconf.py file in the user's Volt project directory
containing all user-defined options. The final configuration, a result of
combining default_conf.py and voltconf.py, are accessible through CONFIG, a
UnifiedConfig instance.

The configurations in default.py and voltconf.py themselves are contained in a
Config instances. There are two Config instances defined in default.py: VOLT,
for containing all internal configurations, and SITE, to contain site-wide
options. Users may override any value in these Configs by declaring the
same Config instance in their voltconf.py.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os

from jinja2 import Environment, FileSystemLoader

from volt.exceptions import ConfigNotFoundError
from volt.utils import path_import, LoggableMixin


DEFAULT_CONF_DIR = os.path.dirname(__file__)
DEFAULT_CONF = 'default_conf'
DEFAULT_WIDGET = 'default_widgets'


class UnifiedConfigContainer(LoggableMixin):

    """Reloadable, iterable lazy container for UnifiedConfig."""

    def __init__(self):
        self._loaded = None
        self._confs = None

    def __getattr__(self, name):
        if self._loaded is None:
            self._load()
        return getattr(self._loaded, name)

    def __setattr__(self, name, value):
        if name in ['_loaded', '_confs']:
            self.__dict__[name] = value
        else:
            if self._loaded is None:
                self._load()
            setattr(self._loaded, name, value)    

    def __dir__(self):
        if self._loaded is None:
            self._load()
        return dir(self._loaded)

    def __iter__(self):
        if self._confs is None:
            self._confs = []
            for item in dir(self._loaded):
                # config objects are all caps
                # so we can shortcut the test instead of isinstance
                if item  == item.upper():
                    self._confs.append(getattr(self._loaded, item))
        return self

    def next(self):
        if self._loaded is None:
            self._load()
        try:
            return self._confs.pop()
        except IndexError:
            # reset for next iteration
            self._confs = None
            raise StopIteration

    def _load(self):
        self._loaded = UnifiedConfig()
        self.logger.debug('loaded: UnifiedConfig')

    def reset(self):
        if self._loaded is not None:
            self._loaded = None
            self._confs = None
            self.logger.debug('reset: UnifiedConfig')


class UnifiedConfig(LoggableMixin):

    """Container class for storing all configurations used in a Volt run.
    
    UnifiedConfig unifies configuration values from volt.config.default_conf
    and the user's voltconf.py.

    """

    def __init__(self):
        """Resolves the unified Config values to use for a Volt run."""
        default = path_import(DEFAULT_CONF, DEFAULT_CONF_DIR)
        root_dir = self.get_root_dir(default.VOLT.USER_CONF)

        user_conf_fname = default.VOLT.USER_CONF.split('.')[0]
        user_widget_fname = default.VOLT.USER_WIDGET.split('.')[0]

        default.VOLT.USER_CONF = os.path.join(root_dir, \
                default.VOLT.USER_CONF)
        default.VOLT.USER_WIDGET = os.path.join(root_dir, \
                default.VOLT.USER_WIDGET)

        # for combining default and user jinja2 filters and tests
        default_filters = default.SITE.FILTERS
        default_tests = default.SITE.TESTS

        # asset dir is always inside template dir
        default.VOLT.ASSET_DIR = os.path.join(default.VOLT.TEMPLATE_DIR, \
                default.VOLT.ASSET_DIR)

        user = path_import(user_conf_fname, root_dir)
        for item in 'VOLT', 'SITE':
            # load from default first and override if present in user
            obj = getattr(default, item)
            if hasattr(user, item):
                obj.update(getattr(user, item))
            for opt in obj:
                # set directory items to absolute paths if endswith _DIR
                if opt.endswith('_DIR'):
                    obj[opt] = os.path.join(root_dir, obj[opt])
                # strip '/'s from URL options
                if opt.endswith('URL'):
                    obj[opt] = obj[opt].strip('/')
            setattr(self, item, obj)

        # set root dir as config in VOLT
        setattr(self.VOLT, 'ROOT_DIR', root_dir)

        self.prep_template(user_widget_fname, default_filters, default_tests)

        self.logger.debug('initialized: UnifiedConfig')


    def prep_template(self, user_widget_fname, default_filters, default_tests):
        """Setups the jinja2 template environment."""

        # set up jinja2 template environment in the SITE Config object
        env = Environment(loader=FileSystemLoader(self.VOLT.TEMPLATE_DIR))
        # combine filters and tests
        self.SITE.FILTERS = tuple(set(self.SITE.FILTERS + default_filters))
        self.SITE.TESTS = tuple(set(self.SITE.TESTS + default_tests))

        # import filters and tests
        default_widget = path_import(DEFAULT_WIDGET, DEFAULT_CONF_DIR)
        try:
            user_widget = path_import(user_widget_fname, self.VOLT.ROOT_DIR)
        except ImportError:
            # set user_widget to None if the user does not define any widgets
            # to prevent getattr below from crashing
            user_widget = None

        for func_type in 'FILTERS', 'TESTS':
            for func_name in getattr(self.SITE, func_type):
                # user-defined functions take precedence
                if hasattr(user_widget, func_name):
                    func = getattr(user_widget, func_name)
                else:
                    func = getattr(default_widget, func_name)

                target = getattr(env, func_type.lower())
                target[func_name] = func

        setattr(self.SITE, 'TEMPLATE_ENV', env)

    @classmethod
    def get_root_dir(self, conf_name, start_dir=None):
        """Returns the root directory of a Volt project.

        conf_name -- User configuration filename
        start_dir -- Starting directory for configuration file lookup.

        Checks the current directory for a Volt settings file. If it is not
        present, parent directories of the current directory is checked until
        a Volt settings file is found. If no Volt settings file is found up to
        '/', raise ConfigNotFoundError.

        """
        # default start_dir setting moved here to facillitate testing
        if not start_dir:
            start_dir = os.getcwd()

        # raise error if search goes all the way to root without any results
        if os.path.dirname(start_dir) == start_dir:
            raise ConfigNotFoundError("Failed to find Volt config file in "
                    "'%s' or its parent directories." % os.getcwd())

        # recurse if config file not found
        if not os.path.exists(os.path.join(start_dir, conf_name)):
            parent = os.path.dirname(start_dir)
            return self.get_root_dir(conf_name, start_dir=parent)

        return start_dir


class Config(dict):

    """Container class for storing configuration options.

    Config is basically a dictionary subclass with predefined class
    attributes and dot-notation access.

    """

    # class attributes
    # so Unit.__init__ doesnt' fail if Config instance don't
    # define these, since these are checked by the base Unit class.
    PROTECTED = ()
    REQUIRED = ()
    FIELDS_AS_DATETIME = ()
    DATETIME_FORMAT = ''
    FIELDS_AS_LIST = ()
    LIST_SEP = ()
    GLOBAL_FIELDS = {}

    def __init__(self, *args, **kwargs):
        """Initializes Config."""
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self


CONFIG = UnifiedConfigContainer()
