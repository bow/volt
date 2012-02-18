"""Entry point for Volt
"""

import argparse
import os
import sys

from volt import __version__, server, util
from volt.config import config


class CustomParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs.
    """
    def error(self, message):
        util.show_error("Error: %s\n" % message.capitalize())
        self.print_usage()
        sys.exit(1)

def build_parsers():
    """Build parser for arguments.
    """
    parser = CustomParser()
    subparsers = parser.add_subparsers(title='subcommands')

    # parser for serve
    server_parser = subparsers.add_parser('serve',
                                          help="serve generated volt site")
    server_parser.add_argument('-p', '--port', dest='server_port',
                               default='8000', type=int,
                               metavar='PORT',
                               help='server port')
    # parser for version
    # bit of a hack, so version can be shown without the "--"
    version_parser = subparsers.add_parser('version',
                                           help="show version number and exit")
    # set function to run dynamically
    for subcmd in ['server', 'version', ]:
        eval('%s_parser' % subcmd).set_defaults(run=eval('run_%s' % subcmd))

    return parser

def run_version():
    """Shows version number.
    """
    print "Volt %s" % __version__

def run_server():
    """Runs the volt server.
    """
    server.run()

def main():
    """Main execution routine.
    """
    # set command-line args accessible package-wide
    config.CMD = build_parsers().parse_args()
    config.CMD.run()
