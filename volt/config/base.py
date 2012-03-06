# -*- coding: utf-8 -*-
"""
----------------
volt.config.base
----------------

Volt configuration base class and methods.

This module provides Config, the class used for containing all configurations
in Volt, and two additional methods for importing Config, import_conf and
grab_config.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
from itertools import ifilter


class ConfigNotFoundError(Exception):
    """Raised when Volt fails to find voltconf.py."""
    pass


class Config(dict):

    """Container class for storing configuration options.

    Config is basically a dictionary subclass with predefined class
    attributes and dot-notation access. Additionally, it also defines
    override(), a method used to subsume values from another Config
    object.

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

    def override(self, conf_obj):
        """Overrides options of the current Config object with another one.

        Args:
            conf_obj - Config object whose values will be used for overriding.

        """
        for key in conf_obj.keys():
            # if key is a dictionary
            # merge the two dictionaries instead of overwriting
            # override occurs if conf_obj (user's config) has a key also
            # present in self (default config)
            # (will this bite me later?)
            if isinstance(conf_obj[key], dict):
                self[key] = dict(self[key].items() + conf_obj[key].items())
            else:
                self[key] = conf_obj[key]


def import_conf(mod, path=False, name=''):
    """Imports a Volt configuration.

    Args:
        mod - Dotted package notation or an absolute path to the configuration
            file.
        path - Boolean indicating if mod is absolute path or dotted package
              notation.
        name - Module name to use if import is done by path.

    """
    if path and os.path.exists(mod):
        from imp import load_source
        return load_source(name,  mod)
    elif not path:
        return __import__(mod, fromlist=[mod.split('.')[-1]])

    raise ImportError("Could not import %s" % mod)

def get_configs(mod):
    """Returns an iterable returning all Config instances in the given module.

    Args
        mod - Module to be searched.

    """
    return ifilter(lambda x: isinstance(getattr(mod, x), Config), dir(mod))


# built-in volt jinja2 filters
def displaytime(time, format):
    """Show time according to format."""
    return time.strftime(format)

JINJA2_FILTERS = {
    'displaytime': displaytime,
}

JINJA2_TESTS = dict()

