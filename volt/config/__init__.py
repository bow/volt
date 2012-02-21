import os
import sys

from volt import ConfigError


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
        self._default = self.import_conf(default_conf)
        self.start_dir = start_dir
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
        user = self.import_conf(self._default.VOLT.USER_CONF, path=True)

        # load default config first, then overwrite by user config
        default_conf_items = [x for x in dir(self._default) if x == x.upper()]
        for item in default_conf_items:
            obj = getattr(self._default, item)
            # if the user-defined configs has a Config object with a
            # same item, merge together and overwrite default config
            if hasattr(user, item):
                obj.override(getattr(user, item))
            # set directory + file items to absolute paths
            # directory + file items has 'DIR' + 'FILE' in their items
            paths = (x for x in obj if x.endswith('_FILE') or x.endswith('_DIR'))
            for opt in paths:
                obj[opt] = os.path.join(self.root, obj[opt])
            setattr(self, item, obj)

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

    def import_conf(self, mod, path=False):
        """Imports a Volt configuration.

        Arguments:
        mod: dotted package notation or an absolute path to the
             configuration file.
        path: boolean indicating if mod is absolute path or dotted package
              notation
        """
        if path and os.path.isabs(mod):
            mod_dir = os.path.dirname(mod)
            mod_file = os.path.basename(mod)
            mod_file = os.path.splitext(mod_file)[0]
            sys.path.append(mod_dir)
            return __import__(mod_file)
        elif not path:
            return __import__(mod, fromlist=[mod.split('.')[-1]])

        raise ImportError("Could not import %s" % mod)


config = Session()
