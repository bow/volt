# Volt base engine

import codecs
import glob
import os
from collections import OrderedDict

import yaml

from volt import ConfigError
from volt.config import config
from volt.config.base import Config


class BaseEngine(object):

    def __init__(self, content_container=None):
        """Initializes the engine

        Arguments:
        config: Engine Config object from volt.config.config
        content_container: content container Class
        """
        if not issubclass(content_container, BaseItem):
            raise TypeError("Engine must be initialized with a content holder class.")

        self.ccontainer = content_container
        self.contents = OrderedDict()

    def open_text(self, fname, mod='r', enc='utf-8'):
        """Open text files with Unicode encoding.
        """
        return codecs.open(fname, mode=mod, encoding=enc)

    def globdir(self, directory, pattern='*', iter=False):
        """Returns glob or iglob results for a given directory.
        """
        pattern = os.path.join(directory, pattern)
        if iter:
            return glob.iglob(pattern)
        return glob.glob(pattern)

    def parse(self):
        """Parses the content, returning BaseItem object.
        """
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
