# Volt custom engine

from volt.config import Config
from volt.utils import cachedproperty
from volt.engine.core import Engine


class MyEngine(Engine):

    # Default engine configurations
    DEFAULTS = Config(
        # URL for all engine content relative to root site URL
        URL = '',

        # Permalink pattern for engine units relative to engine URL
        PERMALINK = '',

        # Directory path for storing engine content
        # relative to the default Volt content directory
        CONTENT_DIR = '',
    )

    # Config instance name in voltconf.py
    USER_CONF_ENTRY = ''

    @cachedproperty
    def units(self):
        pass

    def dispatch(self):
        pass
