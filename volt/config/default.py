# -*- coding: utf-8 -*-
"""
-------------------
volt.config.default
-------------------

Volt default configurations.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


from os.path import join

from volt.config.base import Config, JINJA2_FILTERS


# Changing values in this Config is allowed but not recommended
VOLT = Config(

    # User config file name
    # Used to determine project root
    USER_CONF = 'voltconf.py',

    # Directory paths for content files, templates, and generated site
    # relative to a project root
    CONTENT_DIR = 'content',
    TEMPLATE_DIR = 'templates',
    LAYOUT_DIR = 'layout',
    SITE_DIR = 'site',

    # Ignore patterns
    # Filenames that match this pattern will not be copied from template directory
    # to site directory
    IGNORE_PATTERN = str(),

    # Flag for colored terminal output
    COLORED_TEXT = False,
)


# Default site configurations
SITE = Config(

    # Site name, URL, and description
    TITLE = 'My Volt Site',
    URL = str(),
    DESC = str(),

    # Engines used in generating the site
    # Defaults to none
    ENGINES = tuple(),

    # Plugins used in site generation
    # Tuple of tuples, each containing a string for the plugin file name
    # and list of engine names indicating which engine to target
    # Run according to order listed here
    # Defaults to none
    PLUGINS = (('',[]),),

    # URL to use for pagination
    # This will be used for paginated items after the first one
    # For example, if the pagination URL is 'page', then the second
    # pagination page will have '.../page/2/', the third '.../page/3/', etc.
    PAGINATION_URL = '',

    # Boolean to set if output file names should all be 'index.html' or vary
    # according to the last token in its self.permalist attribute
    # index.html-only outputs allows for nice URLS without fiddling too much
    # with .htaccess
    INDEX_HTML_ONLY = True,
)


# Default configurations for the blog engine
BLOG = Config(

    # URL for all blog content relative to root URL
    URL = 'blog',

    # Blog post permalink, relative to blog URL
    PERMALINK = '{time:%Y/%m/%d}/{slug}',

    # Date and time format used in blog content headers
    # Used for parsing the headers
    # Default is e.g. '2004-03-13 22:10'
    CONTENT_DATETIME_FORMAT = '%Y/%m/%d %H:%M',

    # Date and time format displayed on the generated site
    # Default is e.g. 'Saturday, 13 March 2004'
    DISPLAY_DATETIME_FORMAT = '%A, %d %B %Y',

    # Dictionary containing values to be globally set for all posts
    GLOBAL_FIELDS = dict(),

    # Directory path for storing blog content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, 'blog'),

    # File paths of blog template files relative to a project root
    UNIT_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, 'blog_post.html'),
    PACK_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, 'blog_pagination.html'),

    # Sort order for paginated posts display
    # Valid options are any field present in all units
    # Default order is A-Z (for alphabets) and past-present (for dates)
    # To reverse order just add '-' in front, e.g. '-time'
    SORT = '-time',

    # The number of displayed posts per pagination page
    POSTS_PER_PAGE = 10,

    # Excerpt length (in characters) for paginated items
    EXCERPT_LENGTH = 400,

    # Packs to build for the static site
    # Items in this tuple will be used to set the paginations relative to
    # the blog URL. Items enclosed in '{}' are pulled from the unit values,
    # e.g. 'tag/{tags}' will be expanded to 'tag/x' for x in each tags in the
    # site. These field tokens must be the last token of the pattern.
    # Use an empty string ('') to apply packing to all blog units
    PACKS = ('',),

    # Protected properties
    # These properties must not be defined by any individual blog post header,
    # since they are used internally
    PROTECTED = ('id', 'content', ),

    # Required properties
    # These properties must be defined in each individual blog post header
    REQUIRED = ('title', 'time', ),

    # Fields that would be transformed from string into datetime objects using
    # CONTENT_DATETIME_FORMAT as the pattern
    FIELDS_AS_DATETIME = ('time', ),

    # Fields that would be transformed from string into list objects using
    # LIST_SEP as a separator
    FIELDS_AS_LIST = ('tags', 'categories', ),
    LIST_SEP = ', '
)


# Default configurations for the plain engine
PLAIN = Config(

    # URL for all plain page content relative to root URL
    URL = '/',

    # Plain page permalink, relative to plain page URL
    PERMALINK = '{slug}',

    # Date and time format used in plain page content headers
    # Used for parsing the headers
    # Default is e.g. '2004-03-13 22:10'
    CONTENT_DATETIME_FORMAT = '%Y/%m/%d %H:%M',

    # Date and time format displayed on the generated site
    # Default is e.g. 'Saturday, 13 March 2004'
    DISPLAY_DATETIME_FORMAT = '%A, %d %B %Y',

    # Directory path for storing plain page content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, 'plain'),

    # File paths of plain page template files relative to a project root
    UNIT_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, 'page.html'),

    # Required properties
    # These properties must be defined in each individual plain page unit header
    REQUIRED = ('title', ),

    # Dictionary containing values to be globally set for all posts
    GLOBAL_FIELDS = dict(),

    # Protected properties
    # These properties must not be defined by any individual plain page header,
    # since they are used internally
    PROTECTED = ('id', 'content', 'parent', ),

    # Fields that would be transformed from string into datetime objects using
    # CONTENT_DATETIME_FORMAT as the pattern
    FIELDS_AS_DATETIME = ('time', ),

    # Fields that would be transformed from string into list objects using
    # LIST_SEP as a separator
    FIELDS_AS_LIST = ('tags', 'categories', ),
    LIST_SEP = ', '
)


# Default configurations for the collection engine
COLLECTION = Config(

    # URL for all collection content relative to root URL
    URL = 'collection',

    # Collection permalink, relative to collection URL
    PERMALINK = '{slug}',

    # Directory path for storing collection content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, 'collection'),

    # File paths of collection template files relative to a project root
    UNIT_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, 'single.html'),
    PACK_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, 'multiple.html'),

    # Required properties
    # These properties must be defined for each collection unit individually
    REQUIRED = ('title', 'unit', ),
)


# Settings to be passed on to Jinja2
JINJA2 = Config(

    # Jinja2 filters
    # Dictionary of function names mapped to the functions themselves
    FILTERS = {
        'displaytime': JINJA2_FILTERS['displaytime'],
    },

    # Jinja2 tests
    # Dictionary of function names mapped to the functions themselves
    TESTS = dict(),
)


# Default configurations for plugins
# Empty since by default no plugins are used
PLUGINS = Config()
