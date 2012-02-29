import os
import sys
from itertools import chain

from jinja2 import Environment, FileSystemLoader

from volt import ConfigError
from volt.config.base import Config, get_configs, import_conf


class Session(object):
    """Container class for storing all configurations used in a Volt run.
    """

    def __init__(self, default_conf='volt.config.default', start_dir=os.getcwd()):
        """Initializes Session.

        Arguments:
            default_conf: default configurations, module or absolute path
            start_dir: starting directory for user configuration lookup
        """
        self.py3 = (sys.version_info.major > 2)
        self.start_dir = start_dir
        self._default = import_conf(default_conf)
        self._loaded = False
    
    def __getattr__(self, name):
        if not self._loaded:
            self._load()
        return object.__getattribute__(self, name)

    def _load(self):
        """Loads the session instance.
        """
        # get root and modify path to user conf to absolute path
        self.root = self.get_root(self.start_dir)
        self._default.VOLT.USER_CONF = os.path.join(self.root, \
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
                    obj[opt] = os.path.join(self.root, obj[opt])
                # strip '/'s from URL options
                if opt.endswith('URL'):
                    obj[opt] = obj[opt].strip('/')
            setattr(self, item, obj)

        # set up jinja2 template environment in the SITE Config object
        env = Environment(loader=FileSystemLoader(self.VOLT.TEMPLATE_DIR))

        # add user-defined jinja2 filters
        if hasattr(user, 'JINJA_FILTERS'):
            for func in user.JINJA_FILTERS:
                env.filters[func] = user.JINJA_FILTERS[func]

        # add user-defined jinja2 tests
        if hasattr(user, 'JINJA_TESTS'):
            for func in user.JINJA_TESTS:
                env.tests[func] = user.JINJA_TESTS[func]

        # setattr self jinja2 env
        setattr(self.SITE, 'template_env', env)

        # and set the loaded flag
        self._loaded = True

    def get_root(self, start_dir):
        """Returns the root directory of a Volt project.

        Arguments:
        dir: current directory of Volt execution

        Checks the current directory for a Volt settings file.
        If it is not present, parent directories of the current directory is
        checked until a Volt settings file is found. If no Volt settings
        file is found up to '/', raise ConfigError.
        """
        # raise error if search goes all the way to root without any results
        if os.path.dirname(start_dir) == start_dir:
            raise ConfigError("'%s' is not part of a Volt directory." % \
                    os.getcwd())
        # recurse if config file not found
        if not os.path.exists(os.path.join(start_dir, self._default.VOLT.USER_CONF)):
            parent = os.path.dirname(start_dir)
            return self.get_root(parent)
        return start_dir


config = Session()
