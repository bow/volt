# -*- coding: utf-8 -*-
"""
------------------------------------
volt.plugin.builtins.markdown_parser
------------------------------------

Markdown plugin for Volt units.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os
import sys

try:
    import discount
    has_discount = True
except ImportError:
    import markdown
    has_discount = False

from volt.plugin.core import Plugin


class MarkdownParserPlugin(Plugin):

    """Plugin for transforming markdown syntax to html.

    The plugin can detect whether a unit is formatted using markdown from
    the file extension ('.md' or '.markdown') or if a 'markup' field
    is defined with 'markdown' in the header field. The header field value
    takes precedence over the file extension.

    The discount module is used for conversion to HTML, with the markdown
    module as fallback. This is because markdown processing with discount
    is much faster than by markdown since discount is actually a wrapper
    for Discount, the markdown parser written in C.

    """

    def run(self, engine):
        """Process the given engine."""
        for unit in engine.units:
            # markup lookup, in header field first then file extension
            if hasattr(unit, 'markup'):
                is_markdown = ('markdown' == getattr(unit, 'markup').lower())
            else:
                ext = os.path.splitext(unit.id)[1]
                is_markdown = (ext.lower() in ['.md', '.markdown'])

            # if markdown, then process
            if is_markdown:
                string = getattr(unit, 'content')
                string = self.get_html(string)
                setattr(unit, 'content', string)

    def get_html(self, string):
        """Returns html string of a markdown content.

        string -- string to process
        
        """
        if has_discount:
            if sys.version_info[0] < 3:
                marked = discount.Markdown(string.encode('utf-8'))
                html = marked.get_html_content()
                return html.decode('utf-8')
            else:
                marked = discount.Markdown(string)
                html = marked.get_html_content()
                return html
        else:
            return markdown.markdown(string)
