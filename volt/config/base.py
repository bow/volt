# Volt base configurations file

from os.path import join


class Config(dict):
    """Container class for storing configuration options.
    """
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self

class DefaultConfig(Config):
    """Container class for default configuration options.
    """
    def merge(self, conf_obj):
        for key in conf_obj.keys():
            if key in self:
                self[key] = conf_obj[key]


# General site configurations
SITE = DefaultConfig(

  # Site name, URL, and description
  # No need to add 'http://' in site URL
  TITLE = "My Volt Site",
  URL = "localhost",
  DESC = "",

  # Date and time format used in site content headers
  # Used for parsing the headers
  # Default is e.g. "2004-03-13 22:10"
  CONTENT_DATETIME_FORMAT = "%Y-%m-%d %H:%M",
  # Date and time format displayed on the generated site
  # Default is e.g. "Saturday, 13 March 2004"
  DISPLAY_DATETIME_FORMAT = "%A, %d %B %Y",

  # User config file name
  USER_CONF = "voltconf.py",

  # Directories of content files, templates, and generated site
  CONTENT_DIR = "content",
  TEMPLATE_DIR = "templates",
  SITE_DIR = "site",
)


# Engines switch to set whether an engine is used in site generation or not
ENGINE = DefaultConfig(
  # Default is to turn off all engines
  BLOG = False,
  PAGE = False,
  COLLECTION = False,
)


# Configurations for the blog engine
BLOG = DefaultConfig(

  # Path for all blog posts relative to the site URL
  URL = "blog",

  # Directory for storing blog posts content relative to Volt's root directory
  CONTENT_DIR = join(SITE.CONTENT_DIR, "blog"),

  # Blog posts default author
  # Can be overwritten by conf author individually in post content header
  AUTHOR = "",

  # Blog post permalink
  PERMALINK = "{%Y}/{%m}/{%d}/{slug}",

  # The number of displayed posts per pagination page
  POSTS_PER_PAGE = 10,

  # Default length (in words) of blog post excerpts
  EXCERPT_LENGTH = 50,

  # Default names of blog template files for single blog posts and pagination
  SINGLE_TEMPLATE_FILE = join(SITE.TEMPLATE_DIR, "post.html"),
  MULTIPlE_TEMPLATE_FILE = join(SITE.TEMPLATE_DIR, "pagination.html"),

  # TODO
  # Sort order for paginated posts display
  # Valid options are 'date', 'title', 'category', 'author'
  # Default order is A-Z (for alphabets) and present-past (for dates)
  # To reverse order just add '-' in front, e.g. '-date'
  SORT = ('date', 'title', 'category', 'author', ),

  # Required properties
  # These properties must be defined in each individual blog post header
  REQUIRED = ('title', 'time', ),
)


# Configurations for the page engine
PAGE = DefaultConfig(

  # Path for all pages relative to the site URL
  URL = "page",

  # Directory for storing page content relative to Volt's root directory
  CONTENT_DIR = join(SITE.CONTENT_DIR, "page"),

  # Page permalink
  PERMALINK = "{slug}",

  # Default names of page template file
  TEMPLATE_FILE = join(SITE.TEMPLATE_DIR, "page.html"),

  # Required properties
  # These properties must be defined in each individual page item header
  REQUIRED = ('title', ),
)


# Configurations for the collection engine
COLLECTION = DefaultConfig(

  # Path for all collections relative to the site URL
  URL = "collection",

  # Directory for storing collection content relative to Volt's root directory
  CONTENT_DIR = join(SITE.CONTENT_DIR, "collection"),

  # Page permalink
  PERMALINK = "{slug}",

  # Default names of collection template files for single and multiple items
  SINGLE_TEMPLATE_FILE = join(SITE.TEMPLATE_DIR, "single.html"),
  MULTIPLE_TEMPLATE_FILE = join(SITE.TEMPLATE_DIR, "multiple.html"),

  # Required properties
  # These properties must be defined for each collection items individually
  REQUIRED = ('title', 'item', ),
)
