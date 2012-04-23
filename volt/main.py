# -*- coding: utf-8 -*-
"""
---------
volt.main
---------

Entry point for Volt run.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""

import argparse
import logging
import os
import shutil
import sys
from functools import partial
from datetime import datetime

from volt import VERSION, generator, server
from volt.config import CONFIG
from volt.exceptions import ConfigNotFoundError
from volt.utils import console, LoggableMixin


console = partial(console, format="%s\n", log_time=False)


class ArgParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs."""
    def error(self, message):
        console("\nError: %s" % message, color='red', is_bright=True)
        self.print_usage()
        sys.stdout.write("\n")
        sys.exit(1)


class Runner(LoggableMixin):

    """ Class representing Volt run."""

    def build_logger(self):
        """Initializes package-wide logger."""
        file_format = '[%(asctime)s.%(msecs)03d] %(levelname)-8s %(name)s.%(funcName)s  %(message)s'
        date_format = '%H:%M:%S'
        stderr_format = 'Error: %(message)s'
        if os.name != 'nt':
            stderr_format = '\033[01;31m%s\033[m' % stderr_format

        logger = logging.getLogger('')
        logger.setLevel(CONFIG.SITE.LOG_LEVEL)

        stderr = logging.StreamHandler(sys.stderr)
        stderr.setLevel(logging.ERROR)
        formatter = logging.Formatter(stderr_format, datefmt=date_format)
        stderr.setFormatter(formatter)
        logger.addHandler(stderr)

        if CONFIG.SITE.LOG_LEVEL <= logging.DEBUG:
            # setup file logging
            logfile = logging.FileHandler('volt.log')
            logfile.setLevel(logging.DEBUG)
            formatter = logging.Formatter(file_format, datefmt=date_format)
            logfile.setFormatter(formatter)
            logger.addHandler(logfile)

            with open('volt.log', 'w') as log:
                log.write("#Volt %s Log\n" % VERSION)
                log.write("#Date: %s\n" % datetime.now().strftime("%Y-%m-%d"))
                log.write("#Fields: time, log-level, caller, log-message\n")

    def build_parsers(self):
        """Build parser for arguments."""
        parser = ArgParser()
        subparsers = parser.add_subparsers(title='subcommands')

        # parser for demo
        demo_parser = subparsers.add_parser('demo',
                help="quick Volt demo")

        # parser for ext
        ext_parser = subparsers.add_parser('ext',
                help="adds template for custom engine, plugin, or widget")
        ext_parser.add_argument('template', type=str,
                choices=['engine', 'plugin', 'widget'],
                help="extension type")
        ext_parser.add_argument('--builtin', type=str, dest='builtin', 
                default='', metavar='NAME', help='builtin extension name')

        # parser for gen
        gen_parser = subparsers.add_parser('gen',
                help="generates Volt site using the specified engines")

        # parser for init
        init_parser = subparsers.add_parser('init',
                help="starts a bare Volt project")

        # parser for serve
        serve_parser = subparsers.add_parser('serve',
                help="serve generated volt site")
        serve_parser.add_argument('-p', '--port', dest='server_port',
                                   default='8000', type=int,
                                   metavar='PORT',
                                   help='server port')

        # parser for version
        # bit of a hack, so version can be shown without the "--"
        version_parser = subparsers.add_parser('version',
                                               help="show version number and exit")

        # sets the function to run for each subparser option
        # e.g. subcmd = 'server', it will set the function to run_server
        for subcmd in subparsers.choices.keys():
            eval('%s_parser' % subcmd).set_defaults(run=eval('self.run_%s' % subcmd), name=subcmd)

        return parser

    def run_ext(self):
        """Adds template for engine, plugin, or widget."""
        builtin = CONFIG.CMD.builtin
        template = CONFIG.CMD.template
        volt_dir = os.path.dirname(__file__)
        template_source = os.path.join(volt_dir, 'templates')

        if template == 'widget':
            # if template type is widget, only copy / create if it's not
            # present already
            if not os.path.exists(CONFIG.VOLT.USER_WIDGET):

                # if builtin is not an empty string, get the default widgets
                if builtin:
                    builtin_dir = os.path.join(volt_dir, 'config')
                    shutil.copy2(os.path.join(builtin_dir, 'default_widgets.py'),
                        os.path.join(os.curdir, 'widgets.py'))
                # otherwise get the widget template
                else:
                    shutil.copy2(os.path.join(template_source, 'widgets.py'),
                        os.curdir)
        else:
            template_dir = os.path.join(os.getcwd(), template + 's')

            # create plugin / engine dir in the root dir
            # unless it's there already
            if not os.path.exists(template_dir):
                os.mkdir(template_dir)

            # if builtin is specified, try to get the builtin plugin/engine
            if builtin:
                builtin_dir = os.path.join(volt_dir, template, 'builtins')
                try:
                    if builtin == 'atomic':
                        shutil.copytree(os.path.join(builtin_dir, builtin), \
                                os.path.join(template_dir, builtin))
                    else:
                        shutil.copy2(os.path.join(builtin_dir, builtin + '.py'), \
                                template_dir)
                except IOError:
                    message = "Builtin %s '%s' not found." % (template, builtin)
                    console("Error: %s" % message, color='red', is_bright=True)
                    sys.exit(1)

            # otherwise copy the plugin/engine template
            else:
                template_file = template + '.py'
                if not os.path.exists(os.path.join(template_dir, template_file)):
                    shutil.copy2(os.path.join(template_source, template_file), \
                            template_dir)


    def run_init(self, cmd_name='init'):
        """Starts a new Volt project.

        init -- String, must be 'init' or 'demo', denotes which starting files
                will be copied into the current directory.

        """
        # cmd_name must not be other than 'init' or 'demo'
        assert cmd_name in ['init', 'demo',]

        dir_content = os.listdir(os.curdir)
        if dir_content != [] and dir_content != ['volt.log']:
            message = "'volt %s' must be run inside an empty directory." % cmd_name
            console("Error: %s" % message, color='red', is_bright=True)
            sys.exit(1)

        # get volt installation directory and demo dir
        target_path = os.path.join(os.path.dirname(__file__), 'templates', cmd_name)

        # we only need the first layer to do the copying
        parent_dir, child_dirs, top_files = os.walk(target_path).next()

        # copy all files in parent that's not a .pyc file
        for top in [x for x in top_files if not x.endswith('.pyc')]:
            shutil.copy2(os.path.join(parent_dir, top), os.curdir)
        # copy all child directories
        for child in child_dirs:
            shutil.copytree(os.path.join(parent_dir, child), child)

        if cmd_name == 'init':
            console("\nVolt project started. Have fun!\n", is_bright=True)

    def run_demo(self):
        """Runs a quick demo of Volt."""
        # copy demo files
        self.run_init(cmd_name='demo')
        console("\nPreparing your lightning-speed Volt tour...",  is_bright=True)
        # need to pass arglist to serve, so we'll call main
        main(['serve'])

    def run_gen(self):
        """Generates the static site."""
        if not CONFIG.SITE.ENGINES:
            message = "All engines are inactive -- nothing to generate."
            console(message, is_bright=True, color='red')
        else:
            generator.run()

    def run_serve(self):
        """Generates the static site, and if successful, runs the Volt server."""
        self.run_gen()
        if not os.path.exists(CONFIG.VOLT.SITE_DIR):
            message = "Site directory not found -- nothing to serve."
            console(message, is_bright=True, color='red')
        else:
            server.run()

    def run_version(self):
        """Shows version number."""
        console("Volt %s" % VERSION)


def main(cli_arglist=None):
    """Main execution routine.

    cli_arglist -- List of arguments passed to the command line.

    """
    session = Runner()
    try:
        cmd = session.build_parsers().parse_args(cli_arglist)

        # only build logger if we're not starting a new project
        # or just checking version
        if cmd.name not in ['demo', 'init', 'version']:
            session.build_logger()
            # attach parsed object to the package-wide config
            setattr(CONFIG, 'CMD', cmd)
            os.chdir(CONFIG.VOLT.ROOT_DIR)

        logger = logging.getLogger('main')
        logger.debug("running: %s" % cmd.name)
        cmd.run()
    except ConfigNotFoundError:
        message = "You can only run 'volt %s' inside a Volt project directory." % \
                cmd.name
        console("Error: %s" % message, color='red', is_bright=True)
        console("Start a Volt project by running 'volt init' inside an empty directory.")

        if os.path.exists('volt.log'):
            os.remove('volt.log')

        sys.exit(1)
