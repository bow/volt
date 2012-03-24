# -*- coding: utf-8 -*-
"""
-----------
volt.config
-----------

Volt configuration container module.

This module provides classes for handling configurations used in a Volt site
generation. These configurations are obtained from two files: 1) the default.py
file in this module containining all default configurations necessary for a
Volt site generation, and 2) the voltconf.py file in the user's Volt project
directory containing all user-defined options that may override one or several
default options. The final configuration, a result of combining default.py and
voltconf.py, are accessible through CONFIG, a SessionConfig instance.

The configurations in default.py and voltconf.py themselves are contained in a
Config instance. There are four Config instances defined in default.py: VOLT,
for containing all internal configurations; SITE, to contain site-wide options;
JINJA2_FILTERS, for Jinja2 built-in filters; and JINJA2_TESTS, for Jinja2
built-in tests. Users may override any value in these Configs by declaring the
same Config instance in their voltconf.py.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os
import sys

from jinja2 import Environment, FileSystemLoader

from volt.exceptions import ConfigNotFoundError
from volt.utils import path_import


class SessionConfig(object):

    """Container class for storing all configurations used in a Volt run.
    
    SessionConfig pools in configuration values from volt.config.default and
    the user's voltconf.py. Resolution of which values are used from default.py
    and which one is overriden by voltconf.py is deferred until __getattr__
    is called on a SessionConfig instance. This is done to make SessionConfig
    more testable, since SessionConfig will resolve all '_DIR' options inside
    its Configs to have absolute paths. 
    
    If options resolution is not deferred, the Volt project root-finding method
    will raise an error if SessionConfig is not instantiated in a Volt project
    directory. By making SessionConfig lazy-loads like this, we can instantiate
    it anywhere we want (e.g. in the test directory) and then test its methods
    without doing any Config resolution.

    """

    def __init__(self, default_dir=os.path.dirname(__file__), \
            start_dir=os.getcwd(), default_conf_name='default'):
        """Initializes SessionConfig.

        default_dir -- Absolute directory path of the default configuration.
        start_dir -- Starting directory for user configuration lookup.

        """
        self.py3 = (sys.version_info[0] > 2)
        self.start_dir = start_dir
        self._default = path_import(default_conf_name, default_dir)
        # set flag for lazy-loading
        self._loaded = False
    
    def __getattr__(self, name):
        if not self._loaded:
            self._load()
        return object.__getattribute__(self, name)

    def _load(self):
        """Loads the default and user configurations and resolve the ones to use.

        Prior to Config resolution, _load will try to find the absolute path of
        the directory containing voltconf.py, the user-defined configuration.
        If a path is found, then it will be used to transform all options
        ending with '_FILE' and '_DIR' to point to their absolute paths. This
        method will also normalize 'URL' options, set up the Jinja2 template
        environment to be used throughout Volt site generation, and pools in
        all user-defined Jinja2 tests and filters defined in voltconf.py

        """
        # get root and modify path to user conf to absolute path
        root_dir = self.get_root_dir(self.start_dir)
        self._default.VOLT.USER_CONF = os.path.join(root_dir, \
                self._default.VOLT.USER_CONF)

        # import user-defined configs as a module object
        user_conf_name = os.path.splitext(os.path.basename(\
                self._default.VOLT.USER_CONF))[0]
        user = path_import(user_conf_name, root_dir)

        # name of config objects to get
        target_configs = ['VOLT', 'SITE', 'JINJA2_FILTERS', 'JINJA2_TESTS', ]

        # Configs to process is everything in default + anything in user
        # not present in default
        for item in target_configs:
            # load from default first and override if present in user
            obj = getattr(self._default, item)
            if hasattr(user, item):
                obj.update(getattr(user, item))
            for opt in obj:
                # set directory items to absolute paths
                # directory + file items has 'DIR' + 'FILE' in their items
                if opt.endswith('_DIR'):
                    obj[opt] = os.path.join(root_dir, obj[opt])
                # strip '/'s from URL options
                if opt.endswith('URL'):
                    obj[opt] = obj[opt].strip('/')
            setattr(self, item, obj)

        # set root dir as config in VOLT
        setattr(self.VOLT, 'ROOT_DIR', root_dir)

        # and set the loaded flag to True here
        # so we can start referring to the resolved configs
        self._loaded = True

        # set up jinja2 template environment in the SITE Config object
        env = Environment(loader=FileSystemLoader(self.VOLT.TEMPLATE_DIR))

        # pass jinja2 functions
        config_jinja2 = {'filters': self.JINJA2_FILTERS, 'tests': self.JINJA2_TESTS}
        for type in config_jinja2:
            for func_name in config_jinja2[type]:
                # env.filters or env.tests
                target = getattr(env, type)
                target[func_name] = config_jinja2[type][func_name]

        # setattr self jinja2 env
        setattr(self.SITE, 'TEMPLATE_ENV', env)

    def get_root_dir(self, start_dir):
        """Returns the root directory of a Volt project.

        start_dir -- Starting directory for voltconf.py lookup.

        Checks the current directory for a Volt settings file. If it is not
        present, parent directories of the current directory is checked until
        a Volt settings file is found. If no Volt settings file is found up to
        '/', raise ConfigNotFoundError.

        """
        # raise error if search goes all the way to root without any results
        if os.path.dirname(start_dir) == start_dir:
            raise ConfigNotFoundError("Failed to find Volt config file in "
                    "'%s' or its parent directories." % os.getcwd())

        # recurse if config file not found
        if not os.path.exists(os.path.join(start_dir, \
                self._default.VOLT.USER_CONF)):
            parent = os.path.dirname(start_dir)
            return self.get_root_dir(parent)

        return start_dir


class Config(dict):

    """Container class for storing configuration options.

    Config is basically a dictionary subclass with predefined class
    attributes and dot-notation access.

    """

    # class attributes
    # so Unit.__init__ doesnt' fail if Config instance don't
    # define these, since these are checked by the base Unit class.
    PROTECTED = tuple()
    REQUIRED = tuple()
    FIELDS_AS_DATETIME = tuple()
    CONTENT_DATETIME_FORMAT = str()
    DISPLAY_DATETIME_FORMAT = str()
    FIELDS_AS_LIST = tuple()
    LIST_SEP = str()
    GLOBAL_FIELDS = dict()
    PERMALINK = str()
    PACKS = tuple()

    def __init__(self, *args, **kwargs):
        """Initializes Config."""
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self


CONFIG = SessionConfig()
