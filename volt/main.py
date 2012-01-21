"""Entry point for Volt
"""

import argparse
import os
import sys

from volt import __version__
from volt import server


class CustomParser(argparse.ArgumentParser):
    """Custom parser that prints help message when an error occurs.
    """
    def error(self, message):
        sys.stderr.write('\nerror: %s\n' % message)
        self.print_help()
        print
        sys.exit(2)

def build_parsers():
    """Build parser for arguments.
    """
    parser = CustomParser(version="volt %s" % __version__)
    subparsers = parser.add_subparsers(title='subcommands',
                                      )
    # parser for serve
    server_parser = subparsers.add_parser('serve',
                                          help="serve the 'site' directory if \
                                                  present, otherwise serve \
                                                  current directory",
                                         )
    server_parser.add_argument('-d', '--dir', dest='server_dir',
                               metavar='DIR',
                               help='directory to serve',
                              )
    server_parser.add_argument('-p', '--port', dest='server_port',
                               default='8000', type=int,
                               metavar='PORT',
                               help='server port',
                              )
    server_parser.set_defaults(func=run_server)

    return parser

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
