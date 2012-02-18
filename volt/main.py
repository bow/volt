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
    server_parser.add_argument('volt_dir',
                               default=config.root,
                               nargs='?',
                               metavar='VOLT_DIR',
                               help='volt root directory')
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
        eval('%s_parser' % subcmd).set_defaults(func=eval('run_%s' % subcmd))

    return parser

def run_version(options):
    """Shows version number.
    """
    print "Volt %s" % __version__

def run_server(options):
    """Runs the volt server.
    """
    server.run(options)

def main():
    """Main execution routine.
    """
    parser = build_parsers()
    options = parser.parse_args()
    options.func(options)
