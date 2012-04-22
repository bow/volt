# -*- coding: utf-8 -*-
"""
---------------------------------
volt.plugin.builtins.css_minifier
---------------------------------

CSS minifier plugin.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os

import cssmin

from volt.config import CONFIG, Config
from volt.plugin.core import Plugin


class CssMinifierPlugin(Plugin):

    """Site plugin for minifying CSS."""

    DEFAULTS = Config(
       # resulting minified css name
       OUTPUT_FILE = 'minified.css',
       # directory of output file
       OUTPUT_DIR =  CONFIG.VOLT.SITE_DIR,
       # directory to look for input css files
       SOURCE_DIR = CONFIG.VOLT.SITE_DIR,
       # extension for css files, used in determining which files to minify
       CSS_EXT = '.css',

    )

    USER_CONF_ENTRY = 'PLUGIN_CSS_MINIFIER'

    def run(self, site):
        output_name = self.config.OUTPUT_FILE
        source_dir = self.config.SOURCE_DIR
        output_dir = self.config.OUTPUT_DIR
        css_ext = self.config.CSS_EXT

        # get list of source file names
        source_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) \
                if f != output_name and f.endswith(css_ext)]

        css = ''
        for f in source_files:
            with open(f, 'r') as source_file:
                css += source_file.read()

        with open(os.path.join(output_dir, output_name), 'w') as target_file:
            target_file.write(cssmin.cssmin(css))
