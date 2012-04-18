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
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from volt.config import Config
from volt.plugin.core import Plugin


class SyntaxPlugin(Plugin):

    """Highlights code syntax using pygments.

    This plugin adds the necessary HTML tags to any text enclosed in a
    in a <syntax></syntax> tag so that its syntaxes are highlighted.
    It uses the pygments library to perform this feat, and can highlight any
    language recognized by pygments. If a 'lang=[language]' attribute is not
    specified, it will attempt to guess the language per pygments'
    ``guess_lexer`` function. Optionally, the plugin can also be set to
    highlight any text enclosed in a <pre>(<code>)(</code>)</pre> tag. In this
    case, the lexer will always guess what programming language is being
    highlighted since it is not possible to specify one.

    If the plugin is set to highlight <syntax> tag, it is recommended to be
    run *prior* to any markup processing. Conversely, if the plugin is set
    to highlight <pre>(<code>) tags it should be run *after* markup processing.
    This is because the <pre>(<code>) tags are usually added by the markup
    language. Running the plugin prior to markup processing is still possible
    if the user explicitly sets the <pre>(<code>) tags.

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
        `SYNTAX_TAG`
            Boolean indicating whether to use <syntax> tag or not.
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
            # whether to use the <syntax> (explicit highlighting) tag or
            # <pre><code> tag (implicit highlighting)
            # defaults to False (no <syntax> tag)
            SYNTAX_TAG = False,
    )

    USER_CONF_ENTRY = 'PLUGIN_SYNTAX'

    def run(self, engine):
        """Process the given units."""
        if self.config.SYNTAX_TAG:
            pattern = re.compile(r'(<syntax(.*?)>(.*?)</syntax>)', re.DOTALL)
        else:
            pattern = re.compile(r'(<pre>(?:<code>)?(.*?)(?:</code>)?</pre>)', re.DOTALL)

        for unit in engine.units:
            # get content from unit
            string = getattr(unit, self.config.UNIT_FIELD)
            # highlight syntax in content
            string = self.highlight_code(string, pattern)
            # override original content with syntax highlighted
            setattr(unit, self.config.UNIT_FIELD, string)

        # write syntax highlight css file
        css = HtmlFormatter().get_style_defs('.' + self.config.CSS_CLASS)
        css_file = self.config.CSS_FILE
        with open(css_file, 'w') as target:
            target.write(css)

    def highlight_code(self, string, pattern):
        """Highlights syntaxes in the given string enclosed in a <syntax> tag.

        string -- String containing the code to highlight.
        pattern -- Compiled regex object for highlight pattern matching.
        
        """
        codeblocks = re.findall(pattern, string)
        # results: list of tuples of 2 or 3 items
        # item[0] is the whole code block (syntax tag + code to highlight)
        # item[1] is the programming language (optional, depends on settings)
        # item[2] is the code to highlight

        if codeblocks:
            for codeblock in codeblocks:
                # if enclosed in <syntax>, we have three tuples
                if self.config.SYNTAX_TAG:
                    match, lang, code = codeblock
                # if enclosed in <pre><code>, lang is always None
                else:
                    match, code = codeblock
                    lang = None

                if lang:
                    lang = re.sub(r'\s|lang|=|\"|\'', '', lang)
                    lexer = get_lexer_by_name(lang.lower(), stripall=True)
                else:
                    lexer = guess_lexer(code, stripall=True)

                formatter = HtmlFormatter(linenos=self.config.LINENO, \
                        cssclass=self.config.CSS_CLASS)
                highlighted = highlight(code, lexer, formatter)
                # add 1 arg because replacement should only be done
                # once for each match
                string = string.replace(match, highlighted, 1)

        return string
