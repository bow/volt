"""Collection of useful methods.
"""

import os
import sys
from functools import partial

from volt.config import config


_MARKUP = { '.md': 'markdown',
            '.markdown': 'markdown',
            '.rst': 'rst',
            '.textile': 'textile',
            '.html': 'html',
          }

def show_info(text, c='grey', w='normal'):
    """Colors the text.
    """
    if config.VOLT.COLORED_TEXT:
        color_map = {'black': '30', 'red': '31', 
                     'green': '32', 'yellow': '33', 
                     'blue': '34', 'violet': '35',
                     'cyan': '36', 'grey': '37'}
        weight_map = {'normal': '00', 'bold': '01'}

        text = "\033[%s;%sm%s\033[m" % \
               (weight_map[w], color_map[c], text)

    sys.stderr.write(text)

show_notif, show_warning, show_error = \
    [partial(show_info, c=x) for x in ['cyan', 'yellow', 'red']]
