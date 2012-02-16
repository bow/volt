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
        file is found up to '/', return None.
        """
        current = dir
        if os.path.split(current)[1] == '':
            return
        else:
            if os.path.exists(os.path.join(current, \
                    default.VOLT.USER_CONF)):
                return current
            else:
                parent = os.path.split(current)[0]
                return self.get_root(parent)

    def set_opts(self, module):
        """Sets the values of all Options objects in a loaded module
        as self attributes.

        Argsuments:
        module: loaded config module
        """
        for var in dir(module):
            obj = getattr(module, var)
            if isinstance(obj, Options):
                setattr(self, var, obj)

session = Session()
