# -*- coding: utf-8 -*-
"""
----------
volt.utils
----------

Collection of general handy methods used throughout Volt.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import imp
import os
import sys
from inspect import isclass


COLOR_MAP = {'black': '30', 'red': '31',
             'green': '32', 'yellow': '33',
             'blue': '34', 'violet': '35',
             'cyan': '36', 'grey': '37'}

BRIGHTNESS_MAP = {'normal': '00', 'bold': '01'}


def path_import(name, paths):
    """Imports a module from the specified path.

    name -- String denoting target module name.
    paths -- List of possible absolute directory paths or string of an
        absolute directory path that may contain the target module.

    """
    # convert to list if paths is string
    if isinstance(paths, basestring):
        paths = [paths]
    mod_tuple = imp.find_module(name, paths)
    return imp.load_module(name, *mod_tuple)


def grab_class(mod, cls):
    """Returns a class from the given module that is a subclass of the given
    class.

    mod -- Module to be searched.
    cls -- Parent class of the class to return.

    """
    objs = (getattr(mod, x) for x in dir(mod) if isclass(getattr(mod, x)))
    # return if class is not itself
    for item in objs:
        if item.__name__ != cls.__name__ and issubclass(item, cls):
            return item


def style(string, color='grey', is_bright=False):
    """Formats the color and brightness of the given string for terminal display.
    
    string -- String to color.
    color -- String indicating color.
    is_bright -- Boolean indicating whether to return a bright version of the
                 colored string or not.

    """
    if os.name != 'nt':
        brg = 'bold' if is_bright else 'normal'
        string = "\033[%s;%sm%s\033[m" % (BRIGHTNESS_MAP[brg], \
                COLOR_MAP[color], string)

    sys.stderr.write(string)


def notify(string, chars='=>', color='grey', level=1, is_bright=True):
    """Formats the given string for color terminal display.

    string -- String to color.
    chars -- Characters to append in front of the string
    color -- String indicating color.
    level -- Integer indicating indentation level.
    is_bright -- Boolean indicating whether to return a bright version of the
                 colored string or not.

    """
    if os.name != 'nt':
        brg = 'bold' if is_bright else 'normal'
        string = "\033[%s;%sm%s\033[m %s" % \
               (BRIGHTNESS_MAP[brg], COLOR_MAP[color], chars, string)
    else:
        string = "%s %s" % (chars, string)

    string = '   ' * level + string

    sys.stderr.write(string)
