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

import markdown

from volt.plugin.core import Plugin


PLUGIN = 'MarkdownParser'


class MarkdownParser(Plugin):

    """Plugin for transforming markdown syntax to html.

    The plugin can detect whether a unit is formatted using markdown from
    the file extension ('.md' or '.markdown') or if a 'markup' field
    is defined with 'markdown' in the header field. The header field value
    takes precedence over the file extension.

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
                setattr(unit, 'content', markdown.markdown(string))
