# Volt configurations

from volt.config import Config


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

# Default configurations for plugins
# Empty since by default no plugins are used
PLUGINS = Config()

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
    # Use an empty string ('') to apply pagination to all blog units
    PAGINATIONS = ('',),

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


# Settings to be passed on to Jinja2
JINJA2 = Config(

    # Jinja2 filters
    # Dictionary of function names mapped to the functions themselves
    FILTERS = dict(),

    # Jinja2 tests
    # Dictionary of function names mapped to the functions themselves
    TESTS = dict(),
)
