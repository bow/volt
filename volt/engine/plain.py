# Volt plain engine

from volt.engine import BaseEngine


__name__ = 'plain'


class PlainEngine(BaseEngine):
    """Class for processing plain web pages.
    """

    def run(self):
        # parse plain page units
        self.units = self.process_text_units(self.CONFIG.PLAIN)
        # write them according to template
        self.write_units(self.CONFIG.PLAIN.UNIT_TEMPLATE_FILE)
        return self.units
