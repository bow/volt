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

from volt import __version__, gen, server
from volt.config import CONFIG
from volt.exceptions import ConfigNotFoundError, ContentError
from volt.utils import style


class ArgParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs."""
    def error(self, message):
        style("Error: %s\n" % message.capitalize(), color='red', \
              is_bright=True)
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

def run_init(cmd_name='init'):
    """Starts a new Volt project.

    init -- String, must be 'init' or 'demo', denotes which starting files
            will be copied into the current directory.

    """
    # cmd_name must not be other than 'init' or 'demo'
    assert cmd_name in ['init', 'demo',]

    import os
    import shutil

    if not os.listdir(os.curdir) == []:
        style("'volt %s' must be run inside an empty directory.\n" % \
              cmd_name, color='red', is_bright=True)
        sys.exit(1)

    # get volt installation directory and demo dir
    target_path = os.path.join(os.path.dirname(__file__), "data", cmd_name)

    # we only need the first layer to do the copying
    parent_dir, child_dirs, top_files = os.walk(target_path).next()

    # copy all files in parent
    for top in top_files:
        shutil.copy2(os.path.join(parent_dir, top), os.curdir)
    # copy all child directories
    for child in child_dirs:
        shutil.copytree(os.path.join(parent_dir, child), child)

    if cmd_name == 'init':
        style("Volt project started. Have fun!\n", is_bright=True)

def run_demo():
    """Starts a new project with pre-made demo files, generates the static
    site, and starts the server.

    """
    # copy demo files
    run_init(cmd_name='demo')
    style("\nPreparing your lightning-speed Volt tour...\n", \
            is_bright=True)
    # generate the site
    run_gen()
    # need to pass arglist to serve, so we'll call main
    main(['serve'])

def run_gen():
    """Generates the static site."""
    gen.run()

def run_serve():
    """Runs the volt server."""
    gen.run()
    server.run()

def run_version():
    """Shows version number."""
    print "Volt %s" % __version__

def main(cli_arglist=None):
    """Main execution routine.

    cli_arglist -- List of arguments passed to the command line.

    """
    # set command-line args accessible package-wide
    try:
        CONFIG.CMD = build_parsers().parse_args(cli_arglist)
        CONFIG.CMD.run()
    except ConfigNotFoundError:
        style("You can only run 'volt %s' inside a Volt project "
              "directory.\n" % CONFIG.CMD.name, color='red', is_bright=True)
        style("Start a Volt project by running 'volt init'.\n", color='red',
                is_bright=True)
    except ContentError, e:
        style("Error: %s\n" % e, color='red', is_bright=True)
