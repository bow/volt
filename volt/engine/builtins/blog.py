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

from volt.config import Config
from volt.engine.builtins import TextEngine


class BlogEngine(TextEngine):

    """Engine for processing text files into a blog.

    This engine uses the TextUnit class to represent its resource. Prior to
    writing the output, the TextUnit objects are sorted according to the
    configuration. They are then chained together by adding to each unit
    permalinks that link to the previous and/or next units.

    It also creates paginations according to the settings in voltconf.py

    """

    # Default configurations for the blog engine
    DEFAULTS = Config(

        # URL for all blog content relative to root URL
        URL = '/blog',

        # Blog post permalink, relative to blog URL
        PERMALINK = '{time:%Y/%m/%d}/{slug}',

        # Date and time format used in blog content headers
        # Used for parsing the headers
        # Default is e.g. '2004-03-13 22:10'
        DATETIME_FORMAT = '%Y/%m/%d %H:%M',

        # Dictionary containing values to be globally set for all posts
        GLOBAL_FIELDS = {},

        # Directory path for storing blog content 
        # relative to the default Volt content directory
        CONTENT_DIR = 'blog',

        # File paths of blog template files
        # relative to the default Volt template directory
        UNIT_TEMPLATE = 'blog_unit.html',
        PAGINATION_TEMPLATE = 'blog_pagination.html',

        # Sort order for paginated posts display
        # Valid options are any field present in all units
        # Default order is A-Z (for alphabets) and past-present (for dates)
        # To reverse order just add '-' in front, e.g. '-time'
        SORT_KEY = '-time',

        # The number of displayed posts per pagination page
        UNITS_PER_PAGINATION = 10,

        # Excerpt length (in characters) for paginated items
        EXCERPT_LENGTH = 400,

        # Pagination to build for the static site
        # Items in this tuple will be used to set the paginations relative to
        # the blog URL. Items enclosed in '{}' are pulled from the unit values,
        # e.g. 'tag/{tags}' will be expanded to 'tag/x' for x in each tags in the
        # site. These field tokens must be the last token of the pattern.
        # Use an empty string ('') to apply packing to all blog units
        PAGINATIONS = ('',),

        # Protected properties
        # These properties must not be defined by any individual blog post header,
        # since they are used internally
        PROTECTED = ('id', 'content', ),

        # Required properties
        # These properties must be defined in each individual blog post header
        REQUIRED = ('title', 'time', ),

        # Fields that would be transformed from string into datetime objects using
        # DATETIME_FORMAT as the pattern
        FIELDS_AS_DATETIME = ('time', ),

        # Fields that would be transformed from string into list objects using
        # LIST_SEP as a separator
        FIELDS_AS_LIST = ('tags', 'categories', ),
        LIST_SEP = ', '
    )

    # Config instance name in voltconf.py
    USER_CONF_ENTRY = 'ENGINE_BLOG'

    def preprocess(self):
        # sort units
        self.sort_units()
        # add prev and next permalinks so blog posts can link to each other
        self.chain_units()

    def dispatch(self):
        # write output files
        self.write_units()
        self.write_paginations()
