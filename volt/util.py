"""Collection of useful methods.
"""

import os
import sys
from functools import partial


def is_valid_root(dir):
    """Returns True if the current directory is a valid volt root directory.

    Checks for 'settings.py' and 'site' directory.
    """
    valid_flags = [os.path.join(dir, x) for x in ['settings.py', 'site']]
    return all([os.path.exists(x) for x in valid_flags])

def color(text, c='grey', w='normal'):
    """Colors the text.
    """
    color_map = {
                 'black': '30', 'red': '31', 'green': '32',
                 'yellow': '33', 'blue': '34', 'violet': '35',
                 'cyan': '36', 'grey': '37'
                }
    weight_map = {'normal': '00', 'bold': '01'}

    color_begin = "\033[%s;%sm" % (weight_map[w], color_map[c])

    sys.stderr.write("%s%s\033[m" % (color_begin, text))

normal = color
inform = partial(color, c='green')
notify = partial(color, c='yellow', w='bold')
warn = partial(color, c='red', w='bold')
