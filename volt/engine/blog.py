# Volt blog engine

import os
import re
from datetime import datetime

from volt import ParseError
from volt.config import config
from volt.engine.base import BaseEngine, BaseUnit, MARKUP
from volt.util import markupify


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """
    
    def run(self):
        self.process_units(content_dir=config.BLOG.CONTENT_DIR, conf=config)

    def process_units(self, content_dir, conf=config):
        """Process the individual blog posts.

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
        # also set its URL and absolute file path to be written
        for fname in files:
            self.units[fname] = self.unit_class(fname, header_delim, conf.BLOG)
            # paths and permalinks are not set in BlogUnit to facillitate
            # testing; ideally, each xUnit should only be using one Config instance
            self.set_unit_paths(self.units[fname], conf.VOLT.SITE_DIR, \
                    conf.SITE.URL)


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
        super(BlogUnit, self).__init__(fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, header_delim.split(source.read()))

            # header should be parsed by yaml into dict
            header = self.parse_yaml(read.pop(0))
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, conf.PROTECTED)
                if field in conf.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], conf.CONTENT_DATETIME_FORMAT)
                if field in conf.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], conf.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])
            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(conf.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        self.permalist = self.get_permalist(conf.PERMALINK, conf.URL)
        self.set_markup(MARKUP)

        # process content with the specified markup language
        self.content = markupify(self.content, self.markup)
