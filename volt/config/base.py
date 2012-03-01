import os
import sys
from itertools import ifilter


class Config(dict):
    """Container class for storing configuration options.
    """

    # class attributes
    # so xUnit.__init__ doesnt' fail if Config instance don't
    # define these
    PROTECTED = tuple()
    REQUIRED = tuple()
    FIELDS_AS_DATETIME = tuple()
    CONTENT_DATETIME_FORMAT = str()
    DISPLAY_DATETIME_FORMAT = str()
    FIELDS_AS_LIST = tuple()
    LIST_SEP = str()
    GLOBAL_FIELDS = {}
    PERMALINK = str()

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self

    def override(self, conf_obj):
        """Overrides options of the current Config object with another one.
        """
        for key in conf_obj.keys():
            self[key] = conf_obj[key]


def import_conf(mod, path=False, name=''):
    """Imports a Volt configuration.

    Arguments:
    mod: dotted package notation or an absolute path to the
         configuration file.
    name: module name to use if import is done by path
    path: boolean indicating if mod is absolute path or dotted package
          notation
    """
    if path and os.path.exists(mod):
        from imp import load_source
        return load_source(name,  mod)
    elif not path:
        return __import__(mod, fromlist=[mod.split('.')[-1]])

    raise ImportError("Could not import %s" % mod)

def get_configs(mod):
    """Returns an iterable returning all Config instances in the given module.

    Arguments:
    mod: module to be searched
    """
    return ifilter(lambda x: isinstance(getattr(mod, x), Config), dir(mod))
