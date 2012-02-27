"""Entry point for Volt
"""

import argparse
import os
import shutil
import sys

from volt import util
from volt.config import config
from volt.config.base import import_conf
from volt.engine.base import get_engine, get_unit


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
    conf = config.VOLT
    # prepare output directory
    if os.path.exists(conf.SITE_DIR):
        shutil.rmtree(conf.SITE_DIR)
    shutil.copytree(conf.TEMPLATE_DIR, conf.SITE_DIR, \
            ignore=shutil.ignore_patterns(conf.IGNORE_PATTERN))

    # set up dict for storing all engine units
    # so main index.html can access them
    units = {}

    # generate the site!
    for e in config.SITE.ENGINES:
        # try import engines in user volt project directory first
        try:
            user_eng_path = os.path.join(config.root, 'engine', '%s.py' % e)
            eng_mod = import_conf(user_eng_path, path=True)
        except ImportError:
            eng_mod = import_conf('volt.engine.%s' % e)
        eng_class = get_engine(eng_mod)
        eng_unit = get_unit(eng_mod)
        # run engine and store resulting units in units
        units[eng_mod.__name__] = eng_class(eng_unit).run()

    tpl_file = '_index.html'
    template = config.SITE.template_env.get_template(tpl_file)

    outfile = os.path.join(config.VOLT.SITE_DIR, 'index.html')
    with open(outfile, 'w') as target:
        target.write(template.render(page={}, site=config.SITE, engine=units))

    print 'Success!'

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
