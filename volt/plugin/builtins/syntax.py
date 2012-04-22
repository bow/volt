# -*- coding: utf-8 -*-
"""
---------------------------
volt.plugin.builtins.syntax
---------------------------

Syntax highlighter plugin for Volt.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os
import re

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from volt.config import CONFIG, Config
from volt.plugin.core import Plugin


class SyntaxPlugin(Plugin):

    """Highlights code syntax using pygments.

    This plugin performs syntax highlighting for text enclosed in a <pre> or
    <pre><code> tag. Syntax language can be guessed by the underlying lexer
    (pygments.lexer) or set explicitly using a 'lang' attribute in the
    enclosing <pre> tag.

    For example:

        <pre lang="python">
        print "This is highlighted!"
        </pre>

    will highlight the <pre> tag-enclosed text using a python lexer.

    Ideally, this plugin is run after markup language processing has been done.

    Options for this plugin configurable via voltconf.py are:

        `OUTPUT_FILE`
            String indicating the CSS file output name, defaults to
            syntax_highlight.css in the current directory.

        `OUTPUT_DIR`
            String indicating directory name of output css file, defaults to
            'site'.

        `UNIT_FIELD`
            String indicating which unit field to process, defaults to
            'content'.

        `PYGMENTS_LEXER`
            Dictionary of pygments lexer configurations, as outlined here:
            http://pygments.org/docs/lexers/

        `PYGMENTS_HTML`
            Dictionary of pygments HTMLFormatter configurations, as outlined here:
            http://pygments.org/docs/formatters/

        `EXTRA_CLASS`
            String of list of strings of extra css classes to append to the
            highlighted css selectors.
    """

    DEFAULTS = Config(
            # css output for syntax highlight
            OUTPUT_FILE = 'syntax_highlight.css',
            # directory to output css file
            OUTPUT_DIR = CONFIG.VOLT.SITE_DIR,
            # unit field to process
            UNIT_FIELD =  'content',
            # 
            # options for pygments' lexers, following its defaults
            PYGMENTS_LEXER = {
                'stripall': False,
                'stripnl': True,
                'ensurenl': True,
                'tabsize': 0,
            },
            # options for pygments' HTMLFormatter, following its defaults
            PYGMENTS_HTML = {
                'nowrap': False,
                'full': False,
                'title': '',
                'style': 'default',
                'noclasses': False,
                'classprefix': '',
                'cssclass': 'highlight',
                'csstyles': '',
                'prestyles': '',
                'cssfile': '',
                'noclobber_cssfile': False,
                'linenos': False,
                'hl_lines': [],
                'linenostart': 1,
                'linenostep': 1,
                'linenospecial': 0,
                'nobackground': False,
                'lineseparator': "\n",
                'lineanchors': '',
                'anchorlinenos': False,
            },
            # list of additional css classes for highlighted code
            EXTRA_CLASS = ['.highlight'],
    )

    USER_CONF_ENTRY = 'PLUGIN_SYNTAX'

    def run(self, engine):
        """Process the given units."""
        # build regex patterns
        pattern = re.compile(r'(<pre(.*?)>(?:<code>)?(.*?)(?:</code>)?</pre>)', re.DOTALL)
        lang_pattern = re.compile(r'\s|lang|=|\"|\'')

        output_file = self.config.OUTPUT_FILE
        output_dir = self.config.OUTPUT_DIR
        css_file = os.path.join(output_dir, output_file)

        for unit in engine.units:
            # get content from unit
            string = getattr(unit, self.config.UNIT_FIELD)
            # highlight syntax in content
            string = self.highlight_code(string, pattern, lang_pattern)
            # override original content with syntax highlighted
            setattr(unit, self.config.UNIT_FIELD, string)

        # write syntax highlight css file
        css = HtmlFormatter(**self.config.PYGMENTS_HTML).get_style_defs(self.config.EXTRA_CLASS)
        if not os.path.exists(css_file):
            with open(css_file, 'w') as target:
                target.write(css)

    def highlight_code(self, string, pattern, lang_pattern):
        """Highlights syntaxes in the given string enclosed in a <syntax> tag.

        string -- String containing the code to highlight.
        pattern -- Compiled regex object for highlight pattern matching.
        lang_pattern -- Compiled regex for obtaining language name (if provided)
        
        """
        codeblocks = re.findall(pattern, string)
        # results: list of tuples of 2 or 3 items
        # item[0] is the whole code block (syntax tag + code to highlight)
        # item[1] is the programming language (optional, depends on usage)
        # item[2] is the code to highlight

        if codeblocks:
            for match, lang, code in codeblocks:
                if lang:
                    lang = re.sub(lang_pattern, '', lang)
                    try:
                        lexer = get_lexer_by_name(lang.lower(), **self.config.PYGMENTS_LEXER)
                    # if the lang is not supported or has a typo
                    # let pygments guess the language
                    except ClassNotFound:
                        lexer = guess_lexer(code, **self.config.PYGMENTS_LEXER)
                else:
                    lexer = guess_lexer(code, **self.config.PYGMENTS_LEXER)

                formatter = HtmlFormatter(**self.config.PYGMENTS_HTML)
                highlighted = highlight(code, lexer, formatter)
                # add 1 arg because replacement should only be done
                # once for each match
                string = string.replace(match, highlighted, 1)

        return string
