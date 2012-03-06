# -*- coding: utf-8 -*-
"""
--------
volt.gen
--------

Volt site generator.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
import shutil

from volt import util
from volt.config import CONFIG
from volt.config.base import import_conf
from volt.engine import get_engine
from volt.plugin import get_plugin


class Generator(object):

    """Class representing a Volt run."""

    def activate(self):
        """Runs all the engines and plugins according to the configurations."""
        self.engines = dict()

        for e in CONFIG.SITE.ENGINES:
            try:
                user_eng_path = os.path.join(CONFIG.VOLT.ROOT_DIR, 'engines', '%s.py' % e)
                eng_mod = import_conf(user_eng_path, path=True)
            except ImportError:
                eng_mod = import_conf('volt.engine.%s' % e)
            eng_class = get_engine(eng_mod)
            self.engines[e] = eng_class()

            util.show_notif("  => ", is_bright=True)
            util.show_info("%s engine activated\n" % e.capitalize())
            self.engines[e].activate()

        for p, targets in CONFIG.SITE.PLUGINS:
            try:
                user_plug_path = os.path.join(CONFIG.VOLT.ROOT_DIR, 'plugins', '%s.py' % p)
                plug_mod = import_conf(user_plug_path, path=True)
            except ImportError:
                plug_mod = import_conf('volt.plugin.%s' % p)
            plug_class = get_plugin(plug_mod)

            if plug_class:
                # set default args in CONFIG first before instantiating
                CONFIG.set_plugin_defaults(plug_class.DEFAULT_ARGS)
                plugin = plug_class()

                for target in targets:
                    util.show_warning("  => ", is_bright=True)
                    util.show_info("%s plugin activated -- running on %s units\n" % \
                            (p.capitalize(), target.capitalize()))
                    plugin.run(self.engines[target].units)

        for e in self.engines.values():
            e.dispatch()

        # generate other pages
        tpl_file = 'index.html'
        template = CONFIG.SITE.TEMPLATE_ENV.get_template(tpl_file)

        outfile = os.path.join(CONFIG.VOLT.SITE_DIR, 'index.html')
        if not os.path.exists(outfile):
            with open(outfile, 'w') as target:
                target.write(template.render(page={}, CONFIG=CONFIG))


def run():
    """Generates the site."""

    # prepare output directory
    if os.path.exists(CONFIG.VOLT.SITE_DIR):
        shutil.rmtree(CONFIG.VOLT.SITE_DIR)
    shutil.copytree(CONFIG.VOLT.LAYOUT_DIR, CONFIG.VOLT.SITE_DIR, \
            ignore=shutil.ignore_patterns(CONFIG.VOLT.IGNORE_PATTERN))

    util.show_info("Volt site generation start!\n", is_bright=True)

    # generate the site!
    Generator().activate()
