# -*- coding: utf-8 -*-
"""
---------------------------
volt.plugin.builtins.syntax
---------------------------

Syntax highlighter processor plugin for Volt.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os
import re

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from volt.config import Config
from volt.plugin.core import Plugin


_RE_SYNTAX = re.compile(r'(<syntax:(.*?)>(.*?)</syntax>)', re.DOTALL)


class SyntaxPlugin(Plugin):

    """Highlights code syntax using pygments.

    This processor plugin adds the necessary HTML tags to any text enclosed
    in a <syntax:[language]></syntax> tag so that its syntaxes are highlighted.
    It uses the pygments library to perform this feat, and can highlight any
    language recognized by pygments, so long as it is specified by the
    <syntax:[language]></syntax> tag.

    To avoid unintended results, this plugin should be run before any markup
    processing plugin.

    Options for this plugin configurable via voltconf.py are:

        `CSS_CLASS`
            String indicating the CSS class of the highlighted syntax, defaults
            to 'syntax'.

        `CSS_FILE`
            String indicating absolute path to the CSS file output, defaults to
            syntax_highlight.css in the current directory.

        `LINENO`
            Boolean indicating whether to output line numbers, defaults to
            True.

        `UNIT_FIELD`
            String indicating which unit field to process, defaults to
            'content'.
    """

    DEFAULTS = Config(
            # class name for the highlighted syntax block
            CSS_CLASS = 'syntax',
            # css output for syntax highlight
            # defaults to current directory
            CSS_FILE = os.path.join(os.getcwd(), 'syntax_highlight.css'),
            # whether to output line numbers
            LINENO = True,
            # unit field to process
            UNIT_FIELD =  'content',
    )

    USER_CONF_ENTRY = 'PLUGIN_SYNTAX'

    def run(self, units):
        """Process the given units."""
        for unit in units:
            # get content from unit
            string = getattr(unit, self.config.UNIT_FIELD)
            # highlight syntax in content
            string = self.highlight_syntax(string)
            # override original content with syntax highlighted
            setattr(unit, self.config.UNIT_FIELD, string)

        # write syntax highlight css file
        css = HtmlFormatter().get_style_defs('.' + self.config.CSS_CLASS)
        css_file = self.config.CSS_FILE
        with open(css_file, 'w') as target:
            target.write(css)

    def highlight_syntax(self, string):
        """Highlights syntaxes in the given string.

        string -- string containing the code to highlight.
        
        """
        codeblocks = re.findall(_RE_SYNTAX, string)
        # results: list of tuples of 3 items
        # item[0] is the whole code block (syntax tag + code to highlight)
        # item[1] is the programming language
        # item[2] is the code to highlight

        if codeblocks:
            for match, lang, code in codeblocks:
                lexer = get_lexer_by_name(lang.lower(), stripall=True)
                formatter = HtmlFormatter(linenos=self.config.LINENO, \
                        cssclass=self.config.CSS_CLASS)
                highlighted = highlight(code, lexer, formatter)
                # add 1 arg because replacement should only be done
                # once for each match
                string = string.replace(match, highlighted, 1)

        return string
