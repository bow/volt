# -*- coding: utf-8 -*-
"""
------------------
volt.plugin.atomic
------------------

Atom feed generator plugin.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from volt.config import CONFIG
from volt.plugin import Plugin


class Atomic(Plugin):

    """Creates atom feed of engine units.

    This plugin generates atom feed from the units of its target engine.
    The processed units must have a datetime header field.

    """

    DEFAULT_ARGS = {
        # jinja2 template file
        'ATOM_TEMPLATE_FILE': 'atom_template.xml',
        # output file name
        # by default, the feed is written to the current directory
        'ATOM_OUTPUT_FILE': 'atom.xml',
        # name to put in feed
        'ATOM_NAME': '',
        # unit field containing datetime object
        'ATOM_TIME_FIELD': 'time',
    }

    def run(self, units):
        """Process the given units."""

        # pass in a built-in Volt jinja2 filter to display date
        # and get template
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        env.filters['displaytime'] = CONFIG.JINJA2.FILTERS['displaytime']
        template = env.get_template(CONFIG.PLUGINS.ATOM_TEMPLATE_FILE)

        # set feed generation time
        time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # render and write to output file
        rendered = template.render(units=units[:10], CONFIG=CONFIG, time=time)
        with open(CONFIG.PLUGINS.ATOM_OUTPUT_FILE, 'w') as target:
            target.write(rendered.encode('utf-8'))
