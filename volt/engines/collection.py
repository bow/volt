# Volt collection engine

from volt.config import Config
from volt.engines import Engine
from volt.engines.unit import Unit


class CollectionEngine(Engine):

    # Default configurations for the collection engine
    DEFAULTS = Config(

        # URL for all collection content relative to root URL
        URL = 'collection',

        # Collection permalink, relative to collection URL
        PERMALINK = '{slug}',

        # Directory path for storing collection content 
        # relative to the Volt content directory
        CONTENT_DIR = 'collection',

        # File paths of collection template files
        # relative to the Volt template directory
        UNIT_TEMPLATE = 'single.html',
        PACK_TEMPLATE = 'multiple.html',

        # Required properties
        # These properties must be defined for each collection unit individually
        REQUIRED = ('title', 'unit', ),
    )


class CollectionUnit(Unit):
    pass
