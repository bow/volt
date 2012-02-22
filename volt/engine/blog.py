# Volt blog engine

import os
import re

import yaml

from volt import ParseError
from volt.config import config
from volt.engine.base import BaseEngine, BaseItem
from volt.util import _MARKUP


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """
    
    def run(self):
        self.parse(content_dir=config.BLOG.CONTENT_DIR)

    def parse(self, content_dir):
        # get absolute paths of content files
        content_dir = self.globdir(content_dir, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # set pattern for header delimiter
        header_delim = re.compile(r'^---$', re.MULTILINE)

        # parse each file and fill self.contents with BlogItem-s
        for fname in files:
            self.items[fname] = self.item_class(fname, header_delim)


class BlogItem(BaseItem):
    """Class representation of a single blog post.
    """
    
    def __init__(self, fname, header_delim):

        self.id = fname

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, header_delim.split(source.read()))

            # header should be parsed by yaml into dict
            header = yaml.load(read.pop(0))
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in %s." \
                        % fname)
            # check if no protected header fields is overwritten
            self.check_protected(prot=config.BLOG.PROTECTED, header=header)

            # set blog item file contents as attributes
            for field in header:
                setattr(self, field.lower(), header[field])
            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(req=config.BLOG.REQUIRED)
        # determine content markup language
        self.get_markup(markup_dict=_MARKUP)
        # get datetime object from time strings
        self.process_time(fmt=config.BLOG.CONTENT_DATETIME_FORMAT)
        # transform strings into list
        self.process_into_list(fields=['tags', 'categories'], sep=', ')

        print self.id
        print self.__dict__
