import os


class BaseEngine(object):

    def __init__(self, config):
        """Initializes the engine

        Arguments:
        config: Engine Config object from volt.config.config
        """
        pass

    def parse(self):
        """Parses the content, returning BaseItem object.
        """
        # this should be a generator
        raise NotImplementedError

    def create_dirs(self):
        """Creates all required directories in the site folder.
        """
        raise NotImplementedError

    def build_paths(self):
        """Builds all the required URLs.
        """
        raise NotImplementedError

    def write_single(self):
        """Writes a single BaseItem object to an output file.
        """
        raise NotImplementedError

    def write_multiple(self):
        """Writes an output file composed of multipe BaseItem object.
        """
        raise NotImplementedError

    def start(self):
        """Starts the engine processing.
        """
        raise NotImplementedError


class BaseItem(object):

    def __init__(self, header, content):
        """Initializes a content item.

        Arguments:
        content: item data
        header: item metadata
        """
        pass
