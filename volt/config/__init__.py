import os
import sys

from volt import ConfigError
from volt.config import base


class SessionConfig(object):
    """Container class for storing all configurations used in a Volt run.
    """
    def __init__(self):
        self.root = self.get_root()

        # flag for python version
        self.py3 = (sys.version_info.major > 2)

        # load the user-defined configurations as a module object.
        user_conf = os.path.splitext(base.VOLT.USER_CONF)[0]
        sys.path.append(self.root)
        user =  __import__(user_conf)

        # load default config first, then overwrite by user config
        for name in dir(base):
            obj = getattr(base, name)
            if isinstance(obj, base.DefaultConfig):
                # if the user-defined configs has a Config object with a
                # same name, merge together and overwrite default config
                if hasattr(user, name):
                    obj.merge(getattr(user, name))
                # set directory + file names to absolute paths
                # directory + file names has 'DIR' + 'FILE' in their names
                for opt in obj:
                    if opt.endswith('_DIR') or opt.endswith('_FILE'):
                        obj[opt] = os.path.join(self.root, obj[opt])
                setattr(self, name, obj)

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
        if not os.path.exists(os.path.join(dir, base.VOLT.USER_CONF)):
            parent = os.path.dirname(dir)
            return self.get_root(parent)
        return dir


config = SessionConfig()
