# -*- coding: utf-8 -*-
"""
--------------------------
volt.engine.builtins.plain
--------------------------

Volt Plain Engine.

The plain engine takes text files as resources and writes single web pages.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from volt.config import Config
from volt.engine.builtins import TextEngine


__name__ = 'plain'


class PlainEngine(TextEngine):

    """Class for processing plain web pages."""

    # Default configurations for the plain engine
    DEFAULTS = Config(
        # URL for all plain page content relative to root URL
        URL = 'plain',

        # Plain page permalink, relative to plain page URL
        PERMALINK = '{slug}',

        # Date and time format used in plain page content headers
        # Used for parsing the headers
        # Default is e.g. '2004-03-13 22:10'
        CONTENT_DATETIME_FORMAT = '%Y/%m/%d %H:%M',

        # Date and time format displayed on the generated site
        # Default is e.g. 'Saturday, 13 March 2004'
        DISPLAY_DATETIME_FORMAT = '%A, %d %B %Y',

        # Directory path for storing plain page content
        # relative to the default Volt content directory
        CONTENT_DIR = 'plain',

        # File paths of plain page template files
        # relative to the default Volt template directory
        UNIT_TEMPLATE = 'plain_unit.html',

        # Required properties
        # These properties must be defined in each individual plain page unit header
        REQUIRED = ('title', ),

        # Dictionary containing values to be globally set for all posts
        GLOBAL_FIELDS = dict(),

        # Protected properties
        # These properties must not be defined by any individual plain page header,
        # since they are used internally
        PROTECTED = ('id', 'content', ),

        # Fields that would be transformed from string into datetime objects using
        # CONTENT_DATETIME_FORMAT as the pattern
        FIELDS_AS_DATETIME = ('time', ),

        # Fields that would be transformed from string into list objects using
        # LIST_SEP as a separator
        FIELDS_AS_LIST = ('tags', 'categories', ),
        LIST_SEP = ', ',
    )

    # Config instance name in voltconf.py
    USER_CONF_ENTRY = 'ENGINE_PLAIN'

    def activate(self):
        # parse plain page units
        self.units = self.create_units()

    def dispatch(self):
        # write them according to template
        self.write_units()
