import os
import shutil

from volt.config import CONFIG
from volt.config.base import import_conf
from volt.engine import get_engine


class Generator(object):
    """Class representing a Volt run.
    """
    def activate(self):
        self.engines = {}

        for e in CONFIG.SITE.ENGINES:
            try:
                user_eng_path = os.path.join(CONFIG.ROOT_DIR, 'engines', '%s.py' % e)
                eng_mod = import_conf(user_eng_path, path=True)
            except ImportError:
                eng_mod = import_conf('volt.engine.%s' % e)
            eng_class = get_engine(eng_mod)
            self.engines[e] = eng_class(CONFIG)

            print 'Running %s engine...' % e
            self.engines[e].run()

        # generate other pages
        tpl_file = '_index.html'
        template = CONFIG.SITE.TEMPLATE_ENV.get_template(tpl_file)

        outfile = os.path.join(CONFIG.VOLT.SITE_DIR, 'index.html')
        with open(outfile, 'w') as target:
            target.write(template.render(page={}, site=CONFIG.SITE))


def run():
    """Generates the site.
    """
    # prepare output directory
    if os.path.exists(CONFIG.VOLT.SITE_DIR):
        shutil.rmtree(CONFIG.VOLT.SITE_DIR)
    shutil.copytree(CONFIG.VOLT.TEMPLATE_DIR, CONFIG.VOLT.SITE_DIR, \
            ignore=shutil.ignore_patterns(CONFIG.VOLT.IGNORE_PATTERN))

    # generate the site!
    Generator().activate()

    print 'Success!'
