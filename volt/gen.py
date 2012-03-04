import os
import shutil

from volt.config import CONFIG
from volt.config.base import import_conf
from volt.engine import get_engine
from volt.plugin import get_processor


class Generator(object):
    """Class representing a Volt run.
    """
    def activate(self):
        self.engines = dict()

        for e in CONFIG.SITE.ENGINES:
            try:
                user_eng_path = os.path.join(CONFIG.VOLT.ROOT_DIR, 'engines', '%s.py' % e)
                eng_mod = import_conf(user_eng_path, path=True)
            except ImportError:
                eng_mod = import_conf('volt.engine.%s' % e)
            eng_class = get_engine(eng_mod)
            self.engines[e] = eng_class()

            print 'Parsing units for the %s engine...' % e
            self.engines[e].activate()

        for p, targets in CONFIG.SITE.PLUGINS:
            try:
                user_plug_path = os.path.join(CONFIG.VOLT.ROOT_DIR, 'plugins', '%s.py' % p)
                plug_mod = import_conf(user_plug_path, path=True)
            except ImportError:
                plug_mod = import_conf('volt.plugin.%s' % p)
            plug_class = get_processor(plug_mod)

            if plug_class:
                # set default args in CONFIG first before instantiating
                CONFIG.set_plugin_defaults(plug_class.DEFAULT_ARGS)
                processor = plug_class()

                for target in targets:
                    print 'Running %s processor against the %s units...' % (p, target)
                    processor.process(self.engines[target].units)

        for e in self.engines.values():
            e.dispatch()

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
    shutil.copytree(CONFIG.VOLT.LAYOUT_DIR, CONFIG.VOLT.SITE_DIR, \
            ignore=shutil.ignore_patterns(CONFIG.VOLT.IGNORE_PATTERN))

    # generate the site!
    Generator().activate()

    print 'Success!'
