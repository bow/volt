import os
import sys

from volt import ConfigError
from volt.conf import default
from volt.conf.options import Options


class Session(object):
    """Container class for storing all configurations used in a Volt run.
    """
    def __init__(self):
        self.root = self.get_root()

        # flag for python version
        self.py3 = (sys.version_info.major > 2)

        # load the user-defined configurations as a module object.
        user_conf = os.path.splitext(default.VOLT.USER_CONF)[0]
        sys.path.append(self.root)
        user =  __import__(user_conf)

        # load default config first, then overwrite by user config
        for conf in (default, user):
            self.set_opts(conf)

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
        if not os.path.exists(os.path.join(dir, default.VOLT.USER_CONF)):
            parent = os.path.dirname(dir)
            return self.get_root(parent)
        return dir

    def set_opts(self, module):
        """Sets the values of all Options objects in a loaded module
        as self attributes.

        Argsuments:
        module: loaded config module
        """
        for var in dir(module):
            obj = getattr(module, var)
            if isinstance(obj, Options):
                # set directory + file vars to absolute paths
                # directory + file vars has 'DIR' + 'FILE' in their names
                for opt in obj:
                    if 'DIR' in opt or 'FILE' in opt:
                        obj[opt] = os.path.join(self.root, obj[opt])
                setattr(self, var, obj)

session = Session()
