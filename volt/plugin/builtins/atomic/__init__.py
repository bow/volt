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
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from volt.config import CONFIG, Config
from volt.plugin.core import Plugin


class AtomicPlugin(Plugin):

    """Creates atom feed of engine units.

    This plugin generates atom feed from the units of its target engine.
    The processed units must have a datetime header field.

    Options for this plugin configurable via voltconf.py are:

        `TEMPLATE_FILE`
            Name of the template atom file.

        `OUTPUT_FILE`
            Name of the generated atom file.

        `TIME_FIELD`
            Name of the unit field containing the datetime object used for
            timestamping the feed items.

        `EXCERPT_LENGTH`
            Character length of the excerpt to show in each feed item.

    """

    DEFAULTS = Config(
        # jinja2 template file
        TEMPLATE_FILE = 'atom_template.xml',
        # output file name
        # by default, the feed is written to the current directory
        OUTPUT_FILE = 'atom.xml',
        # unit field containing datetime object
        TIME_FIELD = 'time',
        # excerpt length in feed items
        EXCERPT_LENGTH = 400,
    )

    USER_CONF_ENTRY = 'PLUGIN_ATOMIC'

    def run(self, units):
        """Process the given units."""

        # pass in a built-in Volt jinja2 filter to display date
        # and get template
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        env.filters['displaytime'] = CONFIG.JINJA2_FILTERS['displaytime']
        template = env.get_template(self.config.TEMPLATE_FILE)

        # set feed generation time
        time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # render and write to output file
        rendered = template.render(units=units[:10], CONFIG=CONFIG, time=time)
        with open(self.config.OUTPUT_FILE, 'w') as target:
            target.write(rendered.encode('utf-8'))
