# Volt blog engine

import os
import re
from datetime import datetime

import yaml

from volt import ContentError, ParseError
from volt.config import config
from volt.engine.base import BaseEngine, BaseItem
from volt.util import _MARKUP


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """
    
    def run(self):
        self.parse()

    def parse(self):
        # get absolute paths of content files
        content_dir = self.globdir(config.BLOG.CONTENT_DIR, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # set pattern for header delimiter
        pattern = re.compile(r'^---$', re.MULTILINE)

        # parse each file and fill self.contents with BlogItem-s
        for fname in files:
            with self.open_text(fname) as source:
                # open file and remove whitespaces
                read = filter(None, pattern.split(source.read()))

                # header should be parsed by yaml into dict
                header = yaml.load(read.pop(0))
                if not isinstance(header, dict):
                    raise ParseError("Header format unrecognizable in %s." \
                            % fname)

                # content is everything else after header
                content = read.pop(0).strip()
            
                # store results in an Item class in self.contents
                # with filenames as the key
                self.contents[fname] = self.ccontainer(fname, header, content)


class BlogItem(BaseItem):
    """Class representation of a single blog post.
    """
    
    def __init__(self, fname, header, content):
        self.fname = fname
        self.content = content
        self.header = dict()

        # set all header keys into lowercaps
        for key in header:
            self.header[key.lower()] = header[key]

        self.check_required()
        self.get_markup()
        self.process_into_list()
        self.process_time()

        print self.fname
        print self.header

    def check_required(self):
        """Check if all the required header fields are present.
        """
        for req in config.BLOG.REQUIRED:
            if not req in self.header:
                raise ContentError(\
                        "Required header field '%s' is missing in '%s'" % \
                        (req, self.fname))

    def process_into_list(self, fields=['tags', 'categories'], sep=', '):
        """Transforms a comma-separated tags or categories string into a list.

        Arguments:
        fields: list of fields to transform into list
        sep: field subitem separator
        """
        for field in fields:
            if field in self.header:
                self.header[field] = filter(None, self.header[field].split(sep))

    def process_time(self):
        """Transforms time string into a datetime object.
        """
        if 'time' in self.header:
            self.header['time'] = datetime.strptime(self.header['time'], \
                    config.SITE.CONTENT_DATETIME_FORMAT)

    def get_markup(self, markup_map=_MARKUP):
        """Sets the markup language into a header key-value pair.

        markup_map: dictionary with file extensions as keys and
            their corresponding markup language as values
        """
        if 'markup' not in self.header:
            ext = os.path.splitext(self.fname)[1]
            if ext in markup_map:
                self.header['markup'] = _MARKUP[ext]
            else:
                raise ContentError("Could not determine markup of '%s'" % \
                        self.fname)
