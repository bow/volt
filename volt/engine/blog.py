# Volt blog engine

import os
import re
from datetime import datetime

import yaml

from volt import ParseError
from volt.config import config
from volt.engine.base import BaseEngine, BaseUnit, MARKUP


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """
    
    def run(self):
        self.parse(content_dir=config.BLOG.CONTENT_DIR, conf=config.BLOG)

    def parse(self, content_dir, conf):
        """Parses all files in a directory.

        Arguments:
        content_dir: directory containing files to be parsed
        conf: Config object containing blog options
        """
        # get absolute paths of content files
        content_dir = self.globdir(content_dir, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # set pattern for header delimiter
        header_delim = re.compile(r'^---$', re.MULTILINE)

        # parse each file and fill self.contents with BlogUnit-s
        for fname in files:
            self.units[fname] = self.unit_class(fname, header_delim, conf)


class BlogUnit(BaseUnit):
    """Class representation of a single blog post.
    """
    
    def __init__(self, fname, header_delim, conf):
        """Initializes BlogUnit.

        Arguments:
        fname: blog post filename
        header_delim: compiled regex pattern for header parsing
        conf: Config object containing blog options
        """
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
            self.check_protected(prot=conf.PROTECTED, header=header)

            # set blog unit file contents as attributes
            for field in header:
                if field == 'time':
                    header[field] = datetime.strptime(\
                            header[field], conf.CONTENT_DATETIME_FORMAT)
                setattr(self, field.lower(), header[field])
            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(conf.REQUIRED)
        # determine content markup language
        self.get_markup(MARKUP)
        # transform strings into list
        self.process_into_list(conf.FIELDS_AS_LIST, conf.LIST_SEP)
        # set slug from title
        self.set_slug(self.title)
        # set permalink
        self.set_permalink(conf.PERMALINK, conf.URL)

        print self.id
        print self.__dict__
