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
from traceback import format_exc

from volt import VERSION
from volt.config import CONFIG
from volt.engine.core import Engine
from volt.plugin.core import Plugin
from volt.utils import cachedproperty, console, path_import, write_file, LoggableMixin


console = partial(console, format="[gen] %s  %s\n")


class Site(LoggableMixin):

    """Class representing a Volt site generation run."""

    def __init__(self):
        self.engines = {}
        self.plugins = {}
        self.widgets = {}

    @cachedproperty
    def config(self):
        return CONFIG

    def create(self):
        """Generates the static site.

        This method consists of five distinct steps that results in the final
        site generation:

            1. Output directory preparation: contents from the 'asset'
               directory are copied into a new 'site' directory. If a 'site'
               directory exists prior to the copying, it will be removed.

            2. Engine activation: see the activate_engines method.

            3. Site plugin run and site widget creation: all site plugins are
               run and all site widgets are created

            4. Engine dispatch: see the dispatch_engines method.

            5. Non-engine template processing: site pages that do not belong to
               any engines are then processed. Examples of pages in this
               category are the main index.html and the 404 page. If any engine
               has defined a main index.html, this method will not write
               another index.html.

        """
        self.prepare_output()
        self.activate_engines()
        self.run_plugins()
        self.create_widgets()
        self.dispatch_engines()
        self.write_site_pages()

    def get_processor(self, processor_name, processor_type, \
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
        user_dir = self.config.VOLT.ROOT_DIR
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
        message = "Preparing output directory: %s" % self.config.VOLT.SITE_DIR
        console(message)
        self.logger.debug(message)
        if os.path.exists(self.config.VOLT.SITE_DIR):
            shutil.rmtree(self.config.VOLT.SITE_DIR)
        shutil.copytree(self.config.VOLT.ASSET_DIR, self.config.VOLT.SITE_DIR, \
                ignore=shutil.ignore_patterns(self.config.SITE.IGNORE_PATTERN))

    def activate_engines(self):
        """Activates all engines according to the configurations.

        This method consists of four steps:

            1. Engine priming: all engines listed in CONFIG.SITE.ENGINES are
               loaded. Any engines found in the user directory takes
               precedence over built-in engines. The default settings in each
               engine are then consolidated with the user's setting in
               voltconf.py to yield the final configurations that will be used
               in subsequent engine methods.

            2. Engine preprocessing: all the engines' preprocess() method are
               then run. Any unit processing that happens before the plugins
               are run is done by the preprocess method.

            3. Plugin run: plugins targeting each engine are run to process the
               the target engines' units. Similar to engines, plugins are also
               primed to consolidate the default and user configurations.

            4. Widget creation: widgets for each engine are created and made
               accessible from the any templates.
        """
        for engine_name in self.config.SITE.ENGINES:
            engine_class = self.get_processor(engine_name, 'engines')
            engine = engine_class()
            message = "Engine loaded: %s" % engine_name.capitalize()
            console(message, color='cyan')
            self.logger.debug(message)

            engine.prime()
            self.logger.debug('done: priming %s' % engine_class.__name__)

            engine.preprocess()
            self.logger.debug('done: preprocessing %s' % engine_class.__name__)

            self.run_plugins(engine)
            self.create_widgets(engine)
            self.engines[engine_name] = engine

            # attach engine config values for access in templates
            setattr(self.config, self.engines[engine_name].USER_CONF_ENTRY, \
                    self.engines[engine_name].config)

    def run_plugins(self, engine=None):
        """Runs plugins on engine or site."""
        if engine is not None:
            try:
                plugins = engine.config.PLUGINS
            except AttributeError:
                return
        else:
            plugins = self.config.SITE.PLUGINS

        for plugin in plugins:
            if engine is not None:
                message = "Running engine plugin: %s" % (plugin)
            else:
                message = "Running site plugin: %s" % plugin
            console(message)
            self.logger.debug(message)

            if not plugin in self.plugins:
                try:
                    plugin_class = self.get_processor(plugin, 'plugins')
                except ImportError:
                    message = "Plugin %s not found." % plugin
                    self.logger.error(message)
                    self.logger.debug(format_exc())
                    raise

                self.plugins[plugin] = plugin_class()
                self.plugins[plugin].prime()

            if engine is not None:
                # engine plugins work on their engine instances
                self.plugins[plugin].run(engine)
            else:
                # site plugins work on this site instance
                self.plugins[plugin].run(self)

            # attach plugin config values (if defined) for access in templates
            if self.plugins[plugin].USER_CONF_ENTRY is not None:
                setattr(self.config, self.plugins[plugin].USER_CONF_ENTRY, \
                        self.plugins[plugin].config)

            self.logger.debug("ran: %s plugin" % plugin)

    @cachedproperty
    def widgets_mod(self):
        self.logger.debug('imported: widgets module')
        return path_import('widgets', self.config.VOLT.ROOT_DIR)

    def create_widgets(self, engine=None):
        """Create widgets from engine or site."""
        if engine is not None:
            try:
                widgets = engine.config.WIDGETS
            except AttributeError:
                return
        else:
            widgets = self.config.SITE.WIDGETS

        for widget in widgets:
            if engine is not None:
                message = "Creating engine widget: %s" % widget
            else:
                message = "Creating site widget: %s" % widget
            console(message)
            self.logger.debug(message)

            try:
                widget_func = getattr(self.widgets_mod, widget)
            except AttributeError:
                message = "Widget %s not found." % widget
                self.logger.error(message)
                self.logger.debug(format_exc())
                raise

            if engine is not None:
                # engine widgets work on their engine instances
                self.widgets[widget] = widget_func(engine)
            else:
                # site widgets work on this site instance
                self.widgets[widget] = widget_func(self)
            self.logger.debug("created: %s widget" % widget)

    def dispatch_engines(self):
        """Runs the engines' dispatch method."""
        for engine in self.engines:
            message = "Dispatching %s engine to URL '%s'" % \
                    (engine.lower(), self.engines[engine].config.URL)
            console(message)
            self.logger.debug(message)
            # attach all widgets to each engine, so they're accessible in templates
            self.engines[engine].widgets = self.widgets
            # dispatch them
            self.engines[engine].dispatch()

    def write_site_pages(self):
        """Write site pages, such as a separate index.html or 404.html."""
        for filename in self.config.SITE.PAGES:
            message = "Writing site page: '%s'" % filename
            console(message)
            self.logger.debug(message)

            template = self.config.SITE.TEMPLATE_ENV.get_template(filename)
            path = os.path.join(self.config.VOLT.SITE_DIR, filename)
            if os.path.exists(path):
                message = "File %s already exists. Make sure there are no "\
                          "other entries leading to this file path." % path
                console("Error: %s" % message, is_bright=True, color='red')
                self.logger.error(message)
                sys.exit(1)

            rendered = template.render(page={}, CONFIG=self.config, \
                    widgets=self.widgets)
            if sys.version_info[0] < 3:
                rendered = rendered.encode('utf-8')
            write_file(path, rendered)


def run():
    """Generates the site."""
    logger = logging.getLogger('gen')

    sys.stdout.write("\n")
    message = "Volt %s Static Site Generator" % VERSION
    console(message, is_bright=True)
    logger.debug(message)

    # generate the site!
    start_time = time()
    Site().create()

    message = "Site generated in %.3fs" % (time() - start_time)
    console(message, color='yellow')
    logger.debug(message)
    sys.stdout.write('\n')
