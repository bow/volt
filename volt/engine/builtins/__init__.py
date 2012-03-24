# -*- coding: utf-8 -*-
"""
--------------------
volt.engine.builtins
--------------------

Volt built-in base engines and units.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import glob
import os

from volt.engine.core import _RE_DELIM, Engine, Unit
from volt.exceptions import ParseError


class TextUnit(Unit):

    """Class representation of text resources.

    This unit represents resources whose metadata (YAML header) is contained
    in the same file as the content. Some examples of resources like this 
    is a single blog post or a single plain page. 

    """

    def __init__(self, fname, config):
        """Initializes TextUnit.

        fname -- Absolute path to the source file.
        config -- Config object containing unit options.

        """
        Unit.__init__(self, fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, _RE_DELIM.split(source.read()))
            # header should be parsed by yaml into dict
            try:
                header = self.parse_header(read.pop(0))
            except IndexError:
                raise ParseError("Header not detected in '%s'." % fname)
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, config.PROTECTED)
                if field in config.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], config.CONTENT_DATETIME_FORMAT)
                if field in config.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], config.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])

            # content is everything else after header
            self.content = read.pop(0).strip()

        # check if all required fields are present
        self.check_required(config.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        # and set global values
        for field in config.GLOBAL_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, config.GLOBAL_FIELDS[field])

        # set permalink components
        self.permalist = self.get_permalist(config.PERMALINK, config.URL)
        # set displayed time string
        if hasattr(self, 'time'):
            self.display_time = self.time.strftime(config.DISPLAY_DATETIME_FORMAT)

        # set paths
        paths = self.get_path_and_permalink()
        self.path, self.permalink, self.permalink_abs = paths

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, os.path.basename(self.id))


class TextEngine(Engine):

    """Engine class for processing text units."""

    def create_units(self):
        """Processes units into TextUnit objects and returns them in a list."""
        # get absolute paths of content files
        targets = glob.iglob(os.path.join(self.config.CONTENT_DIR, '*'))
        files = (x for x in targets if os.path.isfile(x))
        units = [TextUnit(fname, self.config) for fname in files]

        return units
