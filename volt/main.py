"""Entry point for Volt
"""

import argparse
import os
import sys

from volt import util
from volt.config import config


__version__ = "0.0.1"


class ArgParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs.
    """
    def error(self, message):
        util.show_error("Error: %s\n" % message.capitalize())
        self.print_usage()
        sys.exit(1)

def build_parsers():
    """Build parser for arguments.
    """
    parser = ArgParser()
    subparsers = parser.add_subparsers(title='subcommands')

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
        eval('%s_parser' % subcmd).set_defaults(run=eval('run_%s' % subcmd))

    return parser

def run_demo():
    """Starts a new project with pre-made demo files, generates the static
    site, and starts the server.
    """
    # TODO
    #run_init()
    #run_gen()
    #run_server()

def run_gen():
    """Generates the static site.
    """
    from volt.engine import BlogEngine, BlogItem, PageEngine, PageItem,\
            CollectionEngine, CollectionItem

    for e in config.SITE.ENGINES:
        eng_class_name = "%sEngine" % e.capitalize()
        eng_item_name = "%sItem" % e.capitalize()
        # try import engines in user volt project directory first
        try:
            eng_mod = __import__("engine.%s" % e, fromlist=[1])
            eng_class = getattr(eng_mod, eng_class_name)
            eng_item = getattr(eng_mod, eng_item_name)
        except ImportError:
            eng_class = eval(eng_class_name)
            eng_item = eval(eng_item_name)
        eng_conf = eval("config.%s" % e.upper())
        eng_class(eng_conf, eng_item).run()

def run_init():
    """Starts a new Volt project.
    """
    # TODO
    pass

def run_serve():
    """Runs the volt server.
    """
    from volt import server
    server.run()

def run_switch():
    """Switches an engine on or off.
    """
    pass

def run_version():
    """Shows version number.
    """
    print "Volt %s" % __version__

def main(cli_arglist=None):
    """Main execution routine.
    """
    # set command-line args accessible package-wide
    config.CMD = build_parsers().parse_args(cli_arglist)
    config.CMD.run()
