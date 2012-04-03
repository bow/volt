# -*- coding: utf-8 -*-
"""
--------
volt.gen
--------

Volt site generator.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os
import shutil
import sys
from inspect import isclass

from volt.config import CONFIG, SessionConfig
from volt.engine.core import Engine
from volt.exceptions import DuplicateOutputError
from volt.plugin.core import Plugin
from volt.utils import path_import, write_file, notify, style


class Generator(object):

    """Class representing a Volt run."""

    def get_processor_class(self, processor_name, processor_type, \
            volt_dir=os.path.dirname(__file__)):
        """Returns the engine or plugin class used in site generation.

        processor_name -- String denoting engine or plugin name.
        processor_type -- String denoting processor type. Must be 'engines'
                          or 'plugins'.
        volt_dir -- String denoting absolute path to Volt's installation
                    directory.
        
        This method tries to load engines or plugins from the user's Volt
        project directory first. Failing that, it will try to import engines
        or plugins from Volt's installation directory.

        """
        # check first if processor type is 'plugins' or 'engines'
        assert processor_type in ['engines', 'plugins'], \
            "Processor type must be 'engines' or 'plugins'"

        # load engine or plugin
        # user_path has priority over volt_path
        user_dir = CONFIG.VOLT.ROOT_DIR
        user_path = os.path.join(user_dir, processor_type)
        volt_path = os.path.join(volt_dir, processor_type[:-1], 'builtins')

        mod = path_import(processor_name, [user_path, volt_path])

        if processor_type == 'engines':
            cls = Engine
        else:
            cls = Plugin

        for obj in (getattr(mod, x) for x in dir(mod) if isclass(getattr(mod, x))):
            if obj.__name__ != cls.__name__ and issubclass(obj, cls):
                return obj

    def start(self):
        """Runs all the engines and plugins according to the configurations.

        This method consists of five distinct steps that results in the final
        site generation:

            1. Engine priming: all engines listed in CONFIG.SITE.ENGINES are
               loaded. Any engines found in the user directory takes
               precedence over built-in engines. The default settings in each
               engine are then consolidated with the user's setting in
               voltconf.py to yield the final configurations that will be used
               in subsequent engine methods.

            2. Engine activation: all the engines' activate() method are then
               run. This usually means the engines' units are parsed and stored
               as its instance attributes in self.units.

            3. Plugin run: plugins listed in CONFIG.SITE.PLUGINS are loaded and
               run against their target engines. Similar to engines, plugins
               are also primed to consolidate the default and user configurations.

            4. Engine dispatch: after the engine units have been processed by
               the plugins, the engines are then dispatched. This will involve
               writing the actual HTML files for each engine. Pack-building, if
               defined for an engine, should be run in this step prior to
               writing.

            5. Non-engine template processing: site pages that do not belong to
               any engines are then processed. Examples of pages in this
               category are the main index.html and the 404 page. If any engine
               has defined a main index.html, this method will not write
               another index.html.

        """
        self.engines = dict()

        # reverse engine-plugin map
        ep_map = dict()
        for engine in CONFIG.SITE.ENGINES:
            ep_map[engine] = [x[0] for x in CONFIG.SITE.PLUGINS if engine in x[1]]

        # prime and activate engines
        for engine in CONFIG.SITE.ENGINES:
            engine_class = self.get_processor_class(engine, 'engines')
            self.engines[engine] = engine_class()
            self.engines[engine].prime()
            self.engines[engine].activate()

            sys.stderr.write('\n')
            notify("Activating %s engine...\n" % \
                    engine.capitalize(), color='cyan')

            plugins = ep_map[engine]
            self.run_plugin(plugins, self.engines[engine].units)

        # dispatch engines
        for engine in self.engines.values():
            engine.dispatch()

        self.write_extra_pages()
        sys.stderr.write('\n')

    def write_extra_pages(self):
        """Write nonengine pages, such as a separate index.html or 404.html."""
        for filename in CONFIG.SITE.EXTRA_PAGES:
            template = CONFIG.SITE.TEMPLATE_ENV.get_template(filename)
            path = os.path.join(CONFIG.VOLT.SITE_DIR, filename)

            if os.path.exists(path):
                raise DuplicateOutputError("'%s' already exists." % path)
            rendered = template.render(page=dict(), CONFIG=CONFIG)
            if sys.version_info[0] < 3:
                rendered = rendered.encode('utf-8')
            write_file(path, rendered)

    def run_plugin(self, plugin_list, units):
        """Runs plugin on the given engine units.

        plugin_list -- List of plugin name.
        units -- List of units from an engine targeted by the plugin.

        """
        for plugin in plugin_list:
            plugin_class = self.get_processor_class(plugin, 'plugins')

            if plugin_class:
                plugin_obj = plugin_class()
                notify("Running %s plugin\n" % plugin.capitalize(), \
                        chars='::', color='yellow', level=2)
                plugin_obj.prime()
                plugin_obj.run(units)


def run():
    """Generates the site."""

    # reload config to reflect any new changes that may have been made
    CONFIG = SessionConfig()

    # prepare output directory
    if os.path.exists(CONFIG.VOLT.SITE_DIR):
        shutil.rmtree(CONFIG.VOLT.SITE_DIR)
    shutil.copytree(CONFIG.VOLT.LAYOUT_DIR, CONFIG.VOLT.SITE_DIR, \
            ignore=shutil.ignore_patterns(CONFIG.SITE.IGNORE_PATTERN))

    style("\nVolt site generation start!\n", is_bright=True)

    if CONFIG.SITE.ENGINES:
        # generate the site!
        Generator().start()
    else:
        notify("All engines are off. Nothing to generate.\n", chars='=>', \
                color='red', level=1)


    style("Site generation finished.\n", is_bright=True)
