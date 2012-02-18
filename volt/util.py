"""Collection of useful methods.
"""

import os
import sys
from functools import partial

from volt.config import config


def volt_path(filepath):
    """Returns the absolute path of a file / directory in a Volt root directory

    Arguments:
    filepath: relative path of the file / directory
    """
    return os.path.join(os.path.abspath(config.root, filepath))

def is_valid_root(dir):
    """Returns True if the current directory is a valid Volt root directory.

    Checks for 'settings.py' and 'site' directory.
    """
    valid_flags = [os.path.join(dir, x) for x in ['settings.py', 'site']]
    return all([os.path.exists(x) for x in valid_flags])

def show_info(text, c='grey', w='normal'):
    """Colors the text.
    """
    color_map = {'black': '30', 'red': '31', 
                 'green': '32', 'yellow': '33', 
                 'blue': '34', 'violet': '35',
                 'cyan': '36', 'grey': '37'}
    weight_map = {'normal': '00', 'bold': '01'}

    colored_text = "\033[%s;%sm%s\033[m" % \
                  (weight_map[w], color_map[c], text)

    sys.stderr.write(colored_text)

show_notif, show_warning, show_error = \
    [partial(show_info, c=x) for x in ['cyan', 'yellow', 'red']]
