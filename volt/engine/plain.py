# Volt plain engine

from volt.engine import Engine


__name__ = 'plain'


class PlainEngine(Engine):
    """Class for processing plain web pages.
    """

    def parse(self):
        # parse plain page units
        self.units = self.process_text_units(self.CONFIG.PLAIN)

    def write(self):
        # write them according to template
        self.write_units(self.CONFIG.PLAIN.UNIT_TEMPLATE_FILE)
