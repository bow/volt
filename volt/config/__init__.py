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
Config instance, available from volt.config.base. There are six Config instances
defined in default.py: VOLT, for containing all internal configurations; SITE,
to contain site-wide options; PLUGINS, for containing configurations about the
plugins used, and three more Config for each of the built-in Engines (BLOG,
PLAIN, and COLLECTION). Users may override any value in these Configs by
declaring the same Config instance in their voltconf.py. In addition to that,
any Config objects declared in voltconf.py not present in default.py are also
captured by SessionConfig. This allows the user to pass in arbitrary Configs
into a Volt site generation, providing them with a flexible and centralized way
of configuring the generated static site.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
import sys
from itertools import chain

from jinja2 import Environment, FileSystemLoader

from volt.config.base import ConfigNotFoundError, get_configs, import_conf


class SessionConfig(object):

    """Container class for storing all configurations used in a Volt run.
    
    SessionConfig pools in configuration values from volt.config.default and
    the user's voltconf.py. Resolution of which values are used from default.py
    and which one is overriden by voltconf.py is deferred until __getattr__
    is called on a SessionConfig instance. This is done to make SessionConfig
    more testable, since SessionConfig will resolve all '_FILE' and '_DIR'
    options inside its Configs to have absolute paths. 
    
    If options resolution is not deferred, the Volt project root-finding method
    will raise an error if SessionConfig is not instantiated in a Volt project
    directory. By making SessionConfig lazy-loads like this, we can instantiate
    it anywhere we want (e.g. in the test directory) and then test its methods
    without doing any Config resolution.

    """

    def __init__(self, default_conf='volt.config.default', start_dir=os.getcwd()):
        """Initializes SessionConfig.

        Keyword Args:
            default_conf - Default configurations, module or absolute path.
            start_dir - Starting directory for user configuration lookup.

        """
        self.py3 = (sys.version_info.major > 2)
        self.start_dir = start_dir
        self._default = import_conf(default_conf)
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
        user = import_conf(self._default.VOLT.USER_CONF, path=True)

        # process default and user-defined Configs
        default_configs = get_configs(self._default)
        user_configs = (x for x in get_configs(user) if x not in default_configs)

        # Configs to process is everything in default + anything in user
        # not present in default
        for item in chain(default_configs, user_configs):
            # try load from default first and override if present in user
            # otherwise load from user
            try:
                obj = getattr(self._default, item)
                if hasattr(user, item):
                    obj.override(getattr(user, item))
            except:
                obj = getattr(user, item)
            for opt in obj:
                # set directory + file items to absolute paths
                # directory + file items has 'DIR' + 'FILE' in their items
                if opt.endswith('_FILE') or opt.endswith('_DIR'):
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

        # pass jinja filters and tests
        for filter in self.JINJA2.FILTERS:
            env.filters[filter] = self.JINJA2.FILTERS[filter]
        for test in self.JINJA2.TESTS:
            env.tests[test] = self.JINJA2.TESTS[test]

        # setattr self jinja2 env
        setattr(self.SITE, 'TEMPLATE_ENV', env)

    def get_root_dir(self, start_dir):
        """Returns the root directory of a Volt project.

        Args:
            start_dir - Starting directory for voltconf.py lookup.

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

    def set_plugin_defaults(self, default_args):
        """Set default values of plugin options in a SessionConfig object.

        Args:
            default_args - dictionary that maps arguments and their default
                values.

        The value for the given name will only be set if the user has not
        set any option with the same name in voltconfig.

        """
        for arg in default_args:
            if not hasattr(self.PLUGINS, arg):
                setattr(self.PLUGINS, arg, default_args[arg])


CONFIG = SessionConfig()
