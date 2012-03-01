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
        css = HtmlFormatter().get_style_defs('.syntax')
        css_file = os.path.join(CONFIG.VOLT.SITE_DIR, 'css')
        with open(css_file, 'w') as target:
            target.write(css)

    def highlight_syntax(string):
        """Highlights the syntaxes in the given string.

        Arguments:
        string: string containing the code to highlight (marked by <syntax> tags)

        Usually string is stored in unit.contents.
        """
        codeblocks = re.finditer(_RE_SYNTAX, string)
        # results: list of tuples of 3 items
        # item[0] is the whole code block (syntax tag + code to highlight)
        # item[1] is the programming language
        # item[2] is the code to highlight

        for match, lang, code in codeblocks:
            lexer = get_lexer_by_name(lang.lower(), stripall=True)
            formatter = HtmlFormatter(linenos=True, cssclass='syntax')
            highlighted = highlight(code, lexer, formatter)
            string = string.replace(match, highlighted, 1)

        return string
