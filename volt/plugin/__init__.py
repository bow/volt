# Volt base plugin classes

from functools import partial

from volt.util import grab_class


class Plugin(object):
    # Set empty DEFAULT_ARGS to prevent generator from complaining
    # in case the plugin subclass does not define DEFAULT_ARGS
    # DEFAULT_ARGS is supposed to hold all values that a user might want to
    # change for any given plugin through his/her voltconf
    DEFAULT_ARGS = dict()


class Processor(Plugin):
    """Plugin class that manipulates units of an engine.
    """
    def process(self, units):
        """Runs the processor.
        """
        raise NotImplementedError("Processor plugins must implement a process() method.")


get_processor = partial(grab_class, cls=Processor)
