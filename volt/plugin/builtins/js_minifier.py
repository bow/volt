# -*- coding: utf-8 -*-
"""
--------------------------------
volt.plugin.builtins.js_minifier
--------------------------------

Javascript minifier plugin.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os

import jsmin

from volt.config import CONFIG, Config
from volt.plugin.core import Plugin


class JsMinifierPlugin(Plugin):

    """Site plugin for minifying javascript."""

    DEFAULTS = Config(
       # resulting minified js name
       OUTPUT_FILE = 'minified.js',
       # directory of output file
       OUTPUT_DIR =  CONFIG.VOLT.SITE_DIR,
       # directory to look for input js files
       SOURCE_DIR = CONFIG.VOLT.SITE_DIR,
       # extension for js files, used in determining which files to minify
       JS_EXT = '.js',

    )

    USER_CONF_ENTRY = 'PLUGIN_JS_MINIFIER'

    def run(self, site):
        output_name = self.config.OUTPUT_FILE
        source_dir = self.config.SOURCE_DIR
        output_dir = self.config.OUTPUT_DIR
        js_ext = self.config.JS_EXT

        # get list of source file names
        source_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) \
                if f != output_name and f.endswith(js_ext)]

        js = ''
        for f in source_files:
            with open(f, 'r') as source_file:
                js += source_file.read()

        with open(os.path.join(output_dir, output_name), 'w') as target_file:
            target_file.write(jsmin.jsmin(js))
