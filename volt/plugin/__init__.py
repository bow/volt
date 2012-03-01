# Volt base plugin classes

from functools import partial

from volt.util import grab_class


class Plugin(object):
   pass


class Processor(Plugin):

    # name of engine to target
    target = ''

    def process(self):
        """Runs the processor.
        """
        raise NotImplementedError("Processor plugins must implement a process() method.")


get_plugin = partial(grab_class, cls=Plugin)
