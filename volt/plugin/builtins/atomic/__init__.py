# -*- coding: utf-8 -*-
"""
---------------------------
volt.plugin.builtins.atomic
---------------------------

Atom feed generator plugin.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os
import sys
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from volt.config import CONFIG, Config
from volt.plugin.core import Plugin


class AtomicPlugin(Plugin):

    """Creates atom feed of engine units.

    This plugin generates atom feed from the units of its target engine.
    The processed units must have a datetime header field.

    Options for this plugin configurable via voltconf.py are:

        `OUTPUT_FILE`
            Name of the generated atom file, defaults to 'atom.xml'.

        `OUTPUT_DIR`
            Name of the directory for the output file, defaults to 'site'.

        `TEMPLATE_FILE`
            Name of the template atom file.

        `TIME_FIELD`
            Name of the unit field containing the datetime object used for
            timestamping the feed items.

        `EXCERPT_LENGTH`
            Character length of the excerpt to show in each feed item.

    """

    DEFAULTS = Config(
        # output file name
        OUTPUT_FILE = 'atom.xml',
        # output directory name
        OUTPUT_DIR = CONFIG.VOLT.SITE_DIR,
        # jinja2 template file
        TEMPLATE_FILE = 'atom_template.xml',
        # unit field containing datetime object
        TIME_FIELD = 'time',
        # excerpt length in feed items
        EXCERPT_LENGTH = 400,
        # how many items in a feed
        FEED_NUM = 10,
    )

    USER_CONF_ENTRY = 'PLUGIN_ATOMIC'

    def run(self, engine):
        """Process the given engine."""

        output_file = self.config.OUTPUT_FILE
        output_dir = self.config.OUTPUT_DIR
        atom_file = os.path.join(output_dir, output_file)

        # pass in a built-in Volt jinja2 filter to display date
        # and get template
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        # use the builtin displaytime filter
        env.filters['displaytime'] = CONFIG.SITE.TEMPLATE_ENV.filters['displaytime']
        template = env.get_template(self.config.TEMPLATE_FILE)

        # set feed generation time
        time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # render and write to output file
        rendered = template.render(units=engine.units[:self.config.FEED_NUM], \
                CONFIG=CONFIG, time=time)
        with open(atom_file, 'w') as target:
            if sys.version_info[0] < 3:
                rendered = rendered.encode('utf-8')
            target.write(rendered)
