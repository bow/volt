# -*- coding: utf-8 -*-
"""
-------------------------
volt.engine.builtins.blog
-------------------------

Volt Blog Engine.

The blog engine takes text files as resources and writes the static files
constituting a simple blog.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
from builtins import filter

import glob
import os

from volt.config import Config
from volt.engine.core import _RE_DELIM, Engine, Unit
from volt.utils import cachedproperty


ENGINE = 'Text'


class TextUnit(Unit):

    """Class representation of text resources.

    This unit represents resources whose metadata (header) is contained
    in the same file as the content. Some examples of resources like this 
    is a single blog post or a single plain page. 

    """

    _re_delim = _RE_DELIM

    def __init__(self, fname, config):
        """Initializes TextUnit.

        fname -- Absolute path to the source file.
        config -- Config object containing unit options.

        """
        super(TextUnit, self).__init__(config)
        self._id = fname

        # parse header and content and check fields
        self.parse_source(self.id)
        self.check_required(self.config.REQUIRED)

        self.logger.debug('created: %s' % self.id)

    @property
    def id(self):
        return self._id

    def parse_source(self, file_path):
        """Parses the header and content from the source file.

        file_path -- Absolute path to source text file.

        """
        with self.open_text(file_path) as source:
            # open file and remove whitespaces
            read = filter(None, self._re_delim.split(source.read(), 2))
            # header should be parsed into dict
            self.parse_header(next(read))
            # content is everything else after header
            self.content = next(read).strip()

        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)

        # and set default values
        for field in self.config.DEFAULT_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, self.config.DEFAULT_FIELDS[field])

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, os.path.basename(self.id))


class TextEngine(Engine):

    """Engine class for processing text units."""

    # Default configurations for the base text engine
    DEFAULTS = Config(
        # Unit filename pattern to match
        UNIT_FNAME_PATTERN = '*'
    )

    unit_class = TextUnit

    @cachedproperty
    def units(self):
        """Units whose source are text files in the filesystem."""
        target_dir = self.config.CONTENT_DIR
        pattern = self.config.UNIT_FNAME_PATTERN
        units = []
        for curdir, children, files in os.walk(target_dir):
            targets = glob.iglob(os.path.join(curdir, pattern))
            files = (x for x in targets if os.path.isfile(x))
            for fname in files:
                units.append(self.unit_class(os.path.join(curdir, fname), self.config))

        if units:
            self.logger.debug('created: %s %s' % (len(units), type(units[0]).__name__))
        return units