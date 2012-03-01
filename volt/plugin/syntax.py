# Volt plugin for syntax highlight


import os
import re

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from volt.config import CONFIG
from volt.plugin import Processor


_RE_SYNTAX = re.compile(r'(<syntax:(.*?)>(.*?)</syntax>)', re.DOTALL)


class SyntaxHighlighter(Processor):
    """Plugin for code highlighting using pygments.
    """
    DEFAULT_ARGS = {
            # class name for the highlighted syntax block
            'SYNTAX_CSS_CLASS': 'syntax',
            # whether to output line numbers
            'SYNTAX_LINENO': True,
            # css output for syntax highlight
            # defaults to current directory
            'SYNTAX_CSS_FILE': os.path.join(os.getcwd(), 'syntax_highlight.css')
    }

    def process(self, units):
        """Process the units

        Arguments:
        units: list containing units to process
        """
        for unit in units:
            # get content from unit
            string = getattr(unit, 'content')
            # highlight syntax in content
            string = self.highlight_syntax(string)
            # override original content with syntax highlighted
            setattr(unit, 'content', string)

        # write syntax highlight css file
        css = HtmlFormatter().get_style_defs('.' + CONFIG.PLUGINS.SYNTAX_CSS_CLASS)
        css_file = CONFIG.PLUGINS.SYNTAX_CSS_FILE
        with open(css_file, 'w') as target:
            target.write(css)

    def highlight_syntax(self, string):
        """Highlights the syntaxes in the given string.

        Arguments:
        string: string containing the code to highlight (marked by <syntax> tags)

        Usually string is stored in unit.contents.
        """
        codeblocks = re.findall(_RE_SYNTAX, string)
        # results: list of tuples of 3 items
        # item[0] is the whole code block (syntax tag + code to highlight)
        # item[1] is the programming language
        # item[2] is the code to highlight

        if codeblocks:
            for match, lang, code in codeblocks:
                lexer = get_lexer_by_name(lang.lower(), stripall=True)
                formatter = HtmlFormatter(linenos=CONFIG.PLUGINS.SYNTAX_LINENO, \
                        cssclass=CONFIG.PLUGINS.SYNTAX_CSS_CLASS)
                highlighted = highlight(code, lexer, formatter)
                string = string.replace(match, highlighted, 1)

        return string
