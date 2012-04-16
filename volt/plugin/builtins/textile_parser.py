# -*- coding: utf-8 -*-
"""
-----------------------------------
volt.plugin.builtins.textile_parser
-----------------------------------

Textile plugin for Volt units.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os

import textile

from volt.plugin.core import Plugin


class TextileParserPlugin(Plugin):

    """Plugin for transforming textile syntax to html."""

    def run(self, engine):
        """Process the given engine."""
        for unit in engine.units:
            if hasattr(unit, 'markup'):
                is_textile = ('textile' == getattr(unit, 'markup').lower())
            else:
                ext = os.path.splitext(unit.id)[1]
                is_textile = (ext.lower() == '.textile')

            if is_textile:
                string = getattr(unit, 'content')
                string = self.get_html(string)
                setattr(unit, 'content', string)

    def get_html(self, string):
        """Returns html string of a textile content.

        string -- string to process
        
        """
        return textile.textile(string)
