import os
import sys

from volt import ConfigError


class Session(object):
    """Container class for storing all configurations used in a Volt run.
    """
    def __init__(self, default_conf='volt.config.default'):
        self.py3 = (sys.version_info.major > 2)
        # lazy loading flag
        self._initialized = False
        self._default = self.import_conf(default_conf)
    
    def __getattr__(self, name):
        if not self._initialized:
            self._initialize()
        return object.__getattribute__(self, name)

    def _initialize(self):
        """Initializes the session instance.
        """
        # get root and add it to sys.path so we can import from it
        self.root = self.get_root()
        sys.path.append(self.root)

        # load the user-defined configurations as a module object.
        # if user config import fails, all config is from default config
        try:
            user_conf = os.path.splitext(self._default.VOLT.USER_CONF)[0]
            user = self.import_conf(user_conf)
        except ImportError:
            user = None

        # load default config first, then overwrite by user config
        default_conf_items = [x for x in dir(self._default) if x == x.upper()]
        for item in default_conf_items:
            obj = getattr(self._default, item)
            # if the user-defined configs has a Config object with a
            # same item, merge together and overwrite default config
            if hasattr(user, item):
                obj.merge(getattr(user, item))
            # set directory + file items to absolute paths
            # directory + file items has 'DIR' + 'FILE' in their items
            paths = (x for x in obj if x.endswith('_FILE') or x.endswith('_DIR'))
            for opt in paths:
                obj[opt] = os.path.join(self.root, obj[opt])
            setattr(self, item, obj)

        self._initialized = True

    def get_root(self, dir=os.getcwd()):
        """Returns the root directory of a Volt project.

        Arguments:
        dir: current directory of Volt execution

        Checks the current directory for a Volt settings file.
        If it is not present, parent directories of the current directory is
        checked until a Volt settings file is found. If no Volt settings
        file is found up to '/', raise ConfigError.
        """
        # raise error if search goes all the way to root without any results
        if os.path.dirname(dir) == dir:
            raise ConfigError("'%s' is not part of a Volt directory." % \
                    os.getcwd())
        # recurse if config file not found
        if not os.path.exists(os.path.join(dir, self._default.VOLT.USER_CONF)):
            parent = os.path.dirname(dir)
            return self.get_root(parent)
        return dir

    def import_conf(self, mod):
        """Imports a Volt configuration.

        Arguments:
        name: dotted module notation or an absolute path to the
              configuration file.
        """
        if os.path.isabs(mod):
            mod_dir = os.path.dirname(mod)
            mod_file = os.path.basename(mod)
            mod_file = os.path.splitext(mod_file)[0]
            sys.path.append(mod_dir)
            return __import__(mod_file)
        return __import__(mod, fromlist=[mod.split('.')[-1]])


config = Session()
