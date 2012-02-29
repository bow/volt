import os
import shutil

from volt.config import CONFIG
from volt.config.base import import_conf
from volt.engine import get_engine


def run():
    """Generates the site.
    """
    conf = CONFIG.VOLT
    # prepare output directory
    if os.path.exists(conf.SITE_DIR):
        shutil.rmtree(conf.SITE_DIR)
    shutil.copytree(conf.TEMPLATE_DIR, conf.SITE_DIR, \
            ignore=shutil.ignore_patterns(conf.IGNORE_PATTERN))

    # set up dict for storing all engine units
    # so main index.html can access them
    units = {}

    # generate the site!
    for e in CONFIG.SITE.ENGINES:
        # try import engines in user volt project directory first
        try:
            user_eng_path = os.path.join(CONFIG.ROOT_DIR, 'engine', '%s.py' % e)
            eng_mod = import_conf(user_eng_path, path=True)
        except ImportError:
            eng_mod = import_conf('volt.engine.%s' % e)
        eng_class = get_engine(eng_mod)
        # run engine and store resulting units in units
        print 'Running %s engine...' % eng_mod.__name__
        units[eng_mod.__name__] = eng_class(CONFIG).run()

    tpl_file = '_index.html'
    template = CONFIG.SITE.TEMPLATE_ENV.get_template(tpl_file)

    outfile = os.path.join(CONFIG.VOLT.SITE_DIR, 'index.html')
    with open(outfile, 'w') as target:
        target.write(template.render(page={}, site=CONFIG.SITE, engine=units))

    print 'Success!'
