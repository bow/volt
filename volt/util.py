"""Collection of useful methods.
"""

import sys
from functools import partial

from volt.config import CONFIG


def show_info(text, c='grey', w='normal'):
    """Colors the text.
    """
    if CONFIG.VOLT.COLORED_TEXT:
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

def markupify(string, lang='html'):
    """Returns the string after processing with the specified markup languaged.

    Arguments:
    string: string to process
    lang: markup language to use; available options are 'html' or 'markdown'
    """
    if lang == 'markdown':
        try:
            import discount
            marked = discount.Markdown(string.encode('utf8')).get_html_content()
            return marked.decode('utf8')
        except ImportError:
            import markdown
            return markdown.markdown(string)
    else:
        return string
