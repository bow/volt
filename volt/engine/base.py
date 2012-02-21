import os

from volt import ConfigError
from volt.config.base import Config
from collections import OrderedDict


class BaseEngine(object):

    def __init__(self, config=None, content_container=None):
        """Initializes the engine

        Arguments:
        config: Engine Config object from volt.config.config
        content_container: content container Class
        """
        if not isinstance(config, Config):
            raise TypeError("Engine must be initialized with a Config object.")

        if not issubclass(content_container, BaseItem):
            raise TypeError("Engine must be initialized with a content holder class.")

        self.config = config
        self.ccontainer = content_container
        self._contents = OrderedDict()

    def parse(self):
        """Parses the content, returning BaseItem object.
        """
        # this should be a generator
        raise NotImplementedError("Subclasses must implement parse().")

    def create_dirs(self):
        """Creates all required directories in the site folder.
        """
        raise NotImplementedError("Subclasses must implement create_dirs().")

    def build_paths(self):
        """Builds all the required URLs.
        """
        raise NotImplementedError("Subclasses must implement build_paths().")

    def write_single(self):
        """Writes a single BaseItem object to an output file.
        """
        raise NotImplementedError("Subclasses must implement write_single().")

    def write_multiple(self):
        """Writes an output file composed of multipe BaseItem object.
        """
        raise NotImplementedError("Subclasses must implement write_multiple().")

    def run(self):
        """Starts the engine processing.
        """
        raise NotImplementedError("Subclasses must implement run().")


class BaseItem(object):

    def __init__(self, header, content):
        """Initializes a content item.

        Arguments:
        content: item data
        header: item metadata
        """
        pass
