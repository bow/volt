# -*- coding: utf-8 -*-
"""
---------
volt.main
---------

Entry point for Volt run.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""


import argparse
import sys

from volt import __version__
from volt import util
from volt.config.base import ConfigNotFoundError
from volt.config import CONFIG
from volt.engine import ContentError


class ArgParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs."""
    def error(self, message):
        util.show_error("Error: %s\n" % message.capitalize())
        self.print_usage()
        sys.exit(1)

def build_parsers():
    """Build parser for arguments."""
    parser = ArgParser()
    subparsers = parser.add_subparsers(title='subcommands')

    # parser for init
    init_parser = subparsers.add_parser('init',
                                        help="starts a bare Volt project")
    # parser for demo
    demo_parser = subparsers.add_parser('demo',
                                        help="quick Volt demo")
    # parser for gen
    gen_parser = subparsers.add_parser('gen',
                                       help="generates Volt site using the specified engines")
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
        eval('%s_parser' % subcmd).set_defaults(run=eval('run_%s' % subcmd), name=subcmd)

    return parser

def run_demo():
    """Starts a new project with pre-made demo files, generates the static
    site, and starts the server.
    """
    import os
    import shutil

    # get volt installation directory and demo dir
    demo_path = os.path.join(os.path.dirname(__file__), "data", "demo")

    # we only need the first layer to do the copying
    targets = os.walk(demo_path).next()

    # only copy if curdir is empty
    if os.listdir('.') == []:
        # copy all files
        for f in targets[2]:
            shutil.copy2(os.path.join(targets[0], f), ".")
        # copy all dirs
        for child_dir in targets[1]:
            shutil.copytree(os.path.join(targets[0], child_dir), child_dir)
        run_gen()
        # need to pass arglist to serve
        main(['serve'])
    else:
        util.show_error("'volt demo' must be run inside an empty directory.\n")

def run_gen():
    """Generates the static site."""
    from volt import gen
    gen.run()
    util.show_info("Site generation finished.\n", is_bright=True)

def run_init():
    """Starts a new Volt project."""
    import os
    import shutil

    # get volt installation directory and init dir
    init_path = os.path.join(os.path.dirname(__file__), "data", "init")

    # we only need the first layer to do the copying
    targets = os.walk(init_path).next()

    # only copy if curdir is empty
    if os.listdir('.') == []:
        # copy all files
        for f in targets[2]:
            shutil.copy2(os.path.join(targets[0], f), ".")
        # copy all dirs
        for child_dir in targets[1]:
            shutil.copytree(os.path.join(targets[0], child_dir), child_dir)
    else:
        util.show_error("'volt init' must be run inside an empty directory.\n")


def run_serve():
    """Runs the volt server."""
    from volt import server
    server.run()

def run_version():
    """Shows version number."""
    print "Volt %s" % __version__

def main(cli_arglist=None):
    """Main execution routine.

    Args:
        cli_arglist - List of arguments passed to the command line.

    """
    # set command-line args accessible package-wide
    try:
        CONFIG.CMD = build_parsers().parse_args(cli_arglist)
        CONFIG.CMD.run()
    except ConfigNotFoundError:
        util.show_error("You can only run 'volt %s' inside a Volt project "
                        "directory.\n" % CONFIG.CMD.name)
        util.show_error("Start a Volt project by running 'volt init'.\n")
    except ContentError, e:
        util.show_error("Error: %s\n" % e)
