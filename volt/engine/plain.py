# Volt page engine

import os

from volt.engine.base import BaseEngine


__name__ = 'plain'


class PlainEngine(BaseEngine):
    """Class for processing plain web pages.
    """

    def run(self):
        self.process_text_units(self.config.PLAIN)
        self.write_units(self.config.PLAIN.TEMPLATE_FILE)
        return self.units
