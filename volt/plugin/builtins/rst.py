# -*- coding: utf-8 -*-
"""
------------------------
volt.plugin.builtins.rst
------------------------

reStructuredText plugin for Volt units.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os

from docutils.core import publish_parts

from volt.plugin.core import Plugin


class RstPlugin(Plugin):

    """Plugin for transforming rST syntax to html."""

    def run(self, units):
        """Process the given units."""
        for unit in units:
            if hasattr(unit, 'markup'):
                is_rst = ('rst' == getattr(unit, 'markup').lower())
            else:
                ext = os.path.splitext(unit.id)[1]
                is_rst = (ext.lower() == '.rst')

            if is_rst:
                string = getattr(unit, 'content')
                string = self.get_html(string)
                setattr(unit, 'content', string)

    def get_html(self, string):
        rst_contents = publish_parts(string, writer_name='html')
        return rst_contents['html_body']
