# -*- coding: utf-8 -*-
"""
--------------
volt.generator
--------------

Volt main site generator.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import logging
import os
import shutil
import sys
from functools import partial
from inspect import isclass
from time import time

from volt import VERSION
from volt.config import CONFIG, SessionConfig
from volt.engine.core import Engine
from volt.plugin.core import Plugin
from volt.utils import console, path_import, write_file, LoggableMixin


console = partial(console, format="[gen] %s  %s\n")


class Generator(LoggableMixin):

    """Class representing a Volt run."""

    def main(self):
        """Generates the static site.

        This method consists of three distinct steps that results in the final
        site generation:

            1. Output directory preparation: contents from the 'asset'
               directory are copied into a new 'site' directory. If a 'site'
               directory exists prior to the copying, it will be removed.

            2. Engine run: see the run_engines method.

            3. Non-engine template processing: site pages that do not belong to
               any engines are then processed. Examples of pages in this
               category are the main index.html and the 404 page. If any engine
               has defined a main index.html, this method will not write
               another index.html.

        """
        self.prepare_output()
        self.run_engines()
        self.write_extra_pages()

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

    def prepare_output(self):
        """Copies the asset directory contents to site directory."""
        message = "Preparing 'site' directory"
        console(message)
        self.logger.debug(message)
        if os.path.exists(CONFIG.VOLT.SITE_DIR):
            shutil.rmtree(CONFIG.VOLT.SITE_DIR)
        shutil.copytree(CONFIG.VOLT.ASSET_DIR, CONFIG.VOLT.SITE_DIR, \
                ignore=shutil.ignore_patterns(CONFIG.SITE.IGNORE_PATTERN))

    def run_engines(self):
        """Runs all engines and plugins according to the configurations.

        This method consists of four steps:

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
        """

        for engine_name in CONFIG.SITE.ENGINES:
            engine_class = self.get_processor_class(engine_name, 'engines')
            self.logger.debug('loaded: %s' % engine_class.__name__)

            engine = engine_class()
            engine.prime()
            self.logger.debug('done: priming %s' % engine_class.__name__)

            message = "Activating engine: %s" % engine_name.capitalize()
            console(message, color='cyan')
            self.logger.debug(message)
            engine.activate()

            self.run_plugins(engine_name, engine.units)

            message = "Dispatching %s engine to URL '%s'" % \
                    (engine_class.__name__[:-6].lower(), engine.config.URL)
            console(message)
            self.logger.debug(message)
            engine.dispatch()

    def run_plugins(self, engine_name, units):
        """Runs plugins on the given engine units.

        engine_name -- String of engine name.
        units -- List of units from an engine targeted by the plugin.

        """
        # run plugins that target the current engine
        plugins = [x[0] for x in CONFIG.SITE.PLUGINS if engine_name in x[1]]
        for plugin in plugins:
            message = "Running plugin: %s" % plugin
            console(message)
            self.logger.debug(message)

            plugin_class = self.get_processor_class(plugin, 'plugins')
            if plugin_class:
                plugin_obj = plugin_class()
                plugin_obj.prime()
                plugin_obj.run(units)

    def write_extra_pages(self):
        """Write nonengine pages, such as a separate index.html or 404.html."""
        for filename in CONFIG.SITE.EXTRA_PAGES:
            message = "Writing extra page: '%s'" % filename
            console(message)
            self.logger.debug(message)

            template = CONFIG.SITE.TEMPLATE_ENV.get_template(filename)
            path = os.path.join(CONFIG.VOLT.SITE_DIR, filename)
            if os.path.exists(path):
                message = "'%s' already exists." % path
                console("Error: %s" % message, is_bright=True, color='red')
                self.logger.error(message)
                sys.exit(1)

            rendered = template.render(page={}, CONFIG=CONFIG)
            if sys.version_info[0] < 3:
                rendered = rendered.encode('utf-8')
            write_file(path, rendered)


def run():
    """Generates the site."""

    logger = logging.getLogger('gen')

    # reload config to reflect any new changes that may have been made
    CONFIG = SessionConfig()

    if CONFIG.SITE.ENGINES:
        sys.stdout.write("\n")
        message = "Volt %s Static Site Generator" % VERSION
        console(message, is_bright=True)
        logger.debug(message)

        # generate the site!
        start_time = time()
        Generator().main()

        message = "Site generated in %.3fs" % (time() - start_time)
        console(message, color='yellow')
        logger.debug(message)
        sys.stdout.write('\n')
    else:
        message = "All engines are off. Nothing to generate."
        console(message, is_bright=True, color='red')
        logger.debug(message)
