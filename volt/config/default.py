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
    PERMALINK = "{%Y}/{%m}/{%d}/{slug}",

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
    SINGLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "post.html"),
    MULTIPlE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "pagination.html"),

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
)


# Default configurations for the page engine
PAGE = Config(

    # URL for all page content relative to root URL
    URL = "page",

    # Page permalink, relative to page URL
    PERMALINK = "{slug}",

    # Directory path for storing page content relative to a project root
    CONTENT_DIR = join(VOLT.CONTENT_DIR, "page"),

    # File paths of page template files relative to a project root
    TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "page.html"),

    # Required properties
    # These properties must be defined in each individual page item header
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
    SINGLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "single.html"),
    MULTIPLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "multiple.html"),

    # Required properties
    # These properties must be defined for each collection item individually
    REQUIRED = ('title', 'item', ),
)
