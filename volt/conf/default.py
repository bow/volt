# Volt default configurations file

import os

from volt.conf.options import Options


__all__ = ['VOLT', 'SITE', 'ENGINES', 'BLOG', 'PAGE', 'COLLECTION', ]


# Default Volt configurations
VOLT = Options(

  # User config file name
  USER_CONF = "voltconf.py",

  # Directories of content files, templates, and generated site
  # All directories are relative to Volt's root directory
  CONTENT_DIR = "content",
  TEMPLATE_DIR = "templates",
  SITE_DIR = "site",
)

# General site configurations
SITE = Options(

  TITLE = "My Volt Site",
  URL = "my.python-volt.org",
  DESC = "",

  # Date and time format used in site content headers
  # Used for parsing the headers
  # Default is e.g. "2004-03-13 22:10"
  CONTENT_DATETIME_FORMAT = "%Y-%m-%d %H:%M",
  # Date and time format displayed on the generated site
  # Default is e.g. "Saturday, 13 March 2004"
  DISPLAY_DATETIME_FORMAT = "%A, %d %B %Y",
)


# Engines switch; sets whether an engine is used in site generation or not
ENGINES = Options(
  BLOG = False,
  PAGE = False,
  COLLECTION = False,
)


# Configurations for the blog engine
BLOG = Options(

  # Path for all blog posts relative to the site URL
  URL = "blog",

  # Directory for storing blog posts content relative to Volt's root directory
  DIR = os.path.join(VOLT.CONTENT_DIR, "blog"),

  # Blog posts default author
  # Can be overwritten by conf author individually in post content header
  AUTHOR = "",

  # Permalink
  PERMALINK = "",

  # The number of displayed posts per pagination page
  POSTS_PER_PAGE = 10,

  # Default length (in words) of blog post excerpts
  EXCERPT_LENGTH = 50,

  # Default names of blog template files for single blog posts and pagination
  POST_TEMPLATE_FILE = os.path.join(VOLT.TEMPLATE_DIR, "post.html",
  PAGINATION_TEMPLATE_FILE = os.path.join(VOLT.TEMPLATE_DIR, "pagination.html"),

)

PAGE = Options(
        
)

COLLECTION = Options(

)
