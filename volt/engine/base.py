# Volt base engine

import codecs
import glob
import os
from collections import OrderedDict
from datetime import datetime

import yaml

from volt import ConfigError, ContentError, ParseError
from volt.config import config


class BaseEngine(object):

    def __init__(self, content_container=None):
        """Initializes the engine

        Arguments:
        content_container: content container class subclassing BaseItem
        """
        if not issubclass(content_container, BaseItem):
            raise TypeError("Engine must be initialized with a content container class.")

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

    def __init__(self, id, header, content):
        """Initializes item object.

        Arguments:
        id: resource identifier, e.g. filename
        header: dictionary of parsed header contents
        content: resource content
        """
        self.id = id
        self.content = content
        self.header = dict()

        # set all header fields into lowercaps
        for field in header:
            self.header[field.lower()] = header[field]

    def check_required(self, reqs):
        """Check if all the required header fields are present.

        Arguments:
        reqs: iterable that contains required header fields
        """
        for req in reqs:
            if not req in self.header:
                raise ContentError(\
                        "Required header field '%s' is missing in '%s'" % \
                        (req, self.id))

    def process_into_list(self, fields=['tags', 'categories'], sep=', '):
        """Transforms a comma-separated tags or categories string into a list.

        Arguments:
        fields: list of fields to transform into list
        sep: field subitem separator
        """
        for field in fields:
            if field in self.header:
                self.header[field] = filter(None, self.header[field].split(sep))

    def process_time(self, time_format):
        """Transforms time string into a datetime object.

        Arguments:
        time_format: time format string
        """
        if 'time' in self.header:
            self.header['time'] = datetime.strptime(self.header['time'], \
                    time_format)

    def get_markup(self, markup_dict):
        """Sets the markup language into a header key-value pair.

        Arguments:
        markup_dict: dictionary with file extensions as keys and
            their corresponding markup language as values
        """
        if 'markup' not in self.header:
            ext = os.path.splitext(self.id)[1]
            if ext in markup_dict:
                self.header['markup'] = markup_dict[ext]
            else:
                raise ContentError("Could not determine markup of '%s'" % \
                        self.id)
