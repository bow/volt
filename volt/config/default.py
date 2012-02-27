# Volt default configurations file

from os.path import join

from volt.config.base import Config


# Volt configurations
# Changing values in this Config is allowed but not recommended
VOLT = Config(

    # User config file name
    # Used to determine project root
    USER_CONF = "voltconf.py",

    # Directory paths for content files, templates, and generated site
    # relative to a project root
    CONTENT_DIR = "content",
    TEMPLATE_DIR = "templates",
    SITE_DIR = "site",

    # Ignore patterns
    # Filenames that match this pattern will not be copied from template directory
    # to site directory
    IGNORE_PATTERN = "_*.html",

    # Flag for colored terminal output
    COLORED_TEXT = False,
)


# Default site configurations
SITE = Config(

    # Site name, URL, and description
    TITLE = "My Volt Site",
    URL = "http://127.0.0.1",
    DESC = "",

    # Engines used in generating the site
    # Defaults to none
    ENGINES = [],
)


# Default configurations for the blog engine
BLOG = Config(

    # URL for all blog content relative to root URL
    URL = "blog",

    # Blog post permalink, relative to blog URL
    PERMALINK = "{time:%Y/%m/%d}/{slug}",

    # Date and time format used in blog content headers
    # Used for parsing the headers
    # Default is e.g. "2004-03-13 22:10"
    CONTENT_DATETIME_FORMAT = "%Y/%m/%d %H:%M",

    # Date and time format displayed on the generated site
    # Default is e.g. "Saturday, 13 March 2004"
    DISPLAY_DATETIME_FORMAT = "%A, %d %B %Y",

    # Blog posts author, can be overwritten in individual blog posts
    AUTHOR = "",

    # The number of displayed posts per pagination page
    POSTS_PER_PAGE = 10,

    # Default length (in words) of blog post excerpts
    EXCERPT_LENGTH = 50,

    # Directory path for storing blog content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, "blog"),

    # File paths of blog template files relative to a project root
    SINGLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "_post.html"),
    MULTIPlE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "_pagination.html"),

    # TODO
    # Sort order for paginated posts display
    # Valid options are 'date', 'title', 'category', 'author'
    # Default order is A-Z (for alphabets) and present-past (for dates)
    # To reverse order just add '-' in front, e.g. '-time'
    SORT = ('time', 'title', 'category', 'author', ),

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
    URL = "/",

    # Plain page permalink, relative to plain page URL
    PERMALINK = "{slug}",

    # Directory path for storing plain page content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, "plain"),

    # File paths of plain page template files relative to a project root
    TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "_plain.html"),

    # Required properties
    # These properties must be defined in each individual plain page unit header
    REQUIRED = ('title', ),
)


# Default configurations for the collection engine
COLLECTION = Config(

    # URL for all collection content relative to root URL
    URL = "collection",

    # Collection permalink, relative to collection URL
    PERMALINK = "{slug}",

    # Directory path for storing collection content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, "collection"),

    # File paths of collection template files relative to a project root
    SINGLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "_single.html"),
    MULTIPLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "_multiple.html"),

    # Required properties
    # These properties must be defined for each collection unit individually
    REQUIRED = ('title', 'unit', ),
)
