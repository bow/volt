# -*- coding: utf-8 -*-
"""
---------
volt.util
---------

Collection of general handy methods used throughout Volt.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import sys
from functools import partial
from inspect import isclass

from volt.config import CONFIG
from volt.config.base import ConfigNotFoundError


def grab_class(mod, cls):
    """Returns a class from the given module that is a subclass of the given class.

    Args:
        mod - Module to be searched.
        cls - Parent class of the class to return.

    """
    objs = (getattr(mod, x) for x in dir(mod) if isclass(getattr(mod, x)))
    # return if class is not itself
    for item in objs:
        if item.__name__ != cls.__name__ and issubclass(item, cls):
            return item

def show_info(string, col='grey', is_bright=False):
    """Returns the string enclosed in color escape codes.

    Args:
        string - String to color.

    Keyword Args:
        col - String indicating color.
        is_bright - Boolean indicating whether to return a bright version
            of the colored string or not.

    This method returns a color code-enclosed string according to the setting
    in CONFIG.VOLT.

    """
    try:
        if CONFIG.VOLT.COLORED_TEXT:
            color_map = {'black': '30', 'red': '31',
                         'green': '32', 'yellow': '33',
                         'blue': '34', 'violet': '35',
                         'cyan': '36', 'grey': '37'}

            brg = 'bold' if is_bright else 'normal'
            bright_map = {'normal': '00', 'bold': '01'}

            string = "\033[%s;%sm%s\033[m" % \
                   (bright_map[brg], color_map[col], string)
    except ConfigNotFoundError:
        pass

    sys.stderr.write(string)

show_notif, show_warning, show_error = \
    [partial(show_info, col=x) for x in ['cyan', 'yellow', 'red']]
show_error = partial(show_error, is_bright=True)
