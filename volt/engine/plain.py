# Volt page engine

import os

from volt.engine.base import BaseEngine


__name__ = 'plain'


class PlainEngine(BaseEngine):
    """Class for processing plain web pages.
    """

    def run(self):
        self.process_text_units(self.config.PLAIN)
        self.write_units()
        return self.units

    def write_units(self):
        """Writes single blog post into its output file.
        """
        template_file = os.path.basename(self.config.PLAIN.TEMPLATE_FILE)
        template_env = self.config.SITE.template_env
        template = template_env.get_template(template_file)

        for unit in self.units:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexptected results
            if os.path.exists(unit.path):
                # TODO: find a better exception name
                raise ContentError("'%s' already exists!" % unit.path)
            os.makedirs(os.path.dirname(unit.path))
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, site=self.config.SITE)
                self.write_output(target, rendered)
