# Volt base engine

import codecs
import glob
import os
import re
from collections import OrderedDict
from datetime import datetime

from volt import ConfigError, ContentError, ParseError
from volt.config import config


MARKUP = { '.md': 'markdown',
           '.markdown': 'markdown',
         }


class BaseEngine(object):

    def __init__(self, item_class=None):
        """Initializes the engine

        Arguments:
        content_container: content container class subclassing BaseItem
        """
        if not issubclass(item_class, BaseItem):
            raise TypeError("Engine must be initialized with a content container class.")

        self.item_class = item_class
        self.items = OrderedDict()

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

    def open_text(self, fname, mod='r', enc='utf-8'):
        """Open text files with Unicode encoding.

        Arguments:
        fname: file name to open
        mod: file mode
        enc: file encoding
        """
        return codecs.open(fname, mode=mod, encoding=enc)

    def check_protected(self, prot, header):
        """Check if none of the defined header fields are in the protected list.
        
        Arguments:
        prot: iterable that contains protected header fields
        header: dictionary resulting from header parsing
        """
        for field in prot:
            if prot in header:
                raise ContentError(\
                        "'%s' should not define the protected header field '%s'" % \
                        (self.id, field))

    def check_required(self, req):
        """Check if all the required header fields are present.

        Arguments:
        req: iterable that contains required header fields
        """
        for field in req:
            if not hasattr(self, field):
                raise ContentError(\
                        "Required header field '%s' is missing in '%s'." % \
                        (field, self.id))

    def process_into_list(self, fields, sep):
        """Transforms a comma-separated tags or categories string into a list.

        Arguments:
        fields: list of fields to transform into list
        sep: field subitem separator
        """
        for field in fields:
            if hasattr(self, field):
                setattr(self, field, filter(None, \
                        getattr(self, field).strip().split(sep)))

    def process_time(self, fmt):
        """Transforms time string into a datetime object.

        Arguments:
        fmt: time format string
        """
        if hasattr(self, 'time'):
            str_time = getattr(self, 'time')
            setattr(self, 'time', datetime.strptime(str_time, fmt))

    def get_markup(self, markup_dict):
        """Sets the markup language into a header key-value pair.

        Arguments:
        markup_dict: dictionary with file extensions as keys and
            their corresponding markup language as values
        """
        if not hasattr(self, 'markup'):
            ext = os.path.splitext(self.id)[1]
            try:
                setattr(self, 'markup', markup_dict[ext])
            except:
                raise ContentError("Could not determine markup of '%s'" % \
                            self.id)
        setattr(self, 'markup', getattr(self, 'markup').lower())
        if getattr(self, 'markup') not in markup_dict.values():
            raise ContentError("Markup language '%s' is not supported." % \
                    getattr(self, 'markup'))

    def set_slug(self, string):
        """Transforms the given string into a slug and set it as a slug instance attribute.

        Arguments:
        string: string to transform into slug
        """
        string = string.strip()

        # remove english articles
        string = re.sub('A\s|An\s', '', string)

        # replace spaces, etc with dash
        string = re.sub(r'\s([A|a]n??)\s|_|\s+', '-', string)

        # remove bad chars
        bad_chars = r'[\!"#\$%&\'\(\)\*\+\,\./:;<=>\?@\[\\\]\^`\{\|\}~]'
        string = re.sub(bad_chars, '', string)
        # warn if there are non-ascii chars
        assert string.decode('utf8') == string

        # slug should not begin or end with dash or contain multiple dashes
        string = re.sub(r'^-+|-+$', '', string)
        string = re.sub(r'-+', '-', string)

        # raise exception if slug results in an empty string
        if not string:
            raise ContentError("Slug for '%s' is an empty string." % self.id)

        setattr(self, 'slug', string.lower())
