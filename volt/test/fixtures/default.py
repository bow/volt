# Volt default configurations file fixture

from os.path import join

from volt.config.base import DefaultConfig


VOLT = DefaultConfig(
    USER_CONF = "voltconf.py",
    CONTENT_DIR = "content",
    TEMPLATE_DIR = "templates",
    SITE_DIR = "site",
    CONTENT_DATETIME_FORMAT = "%Y-%m-%d %H:%M",
    DISPLAY_DATETIME_FORMAT = "%A, %d %B %Y",
)

SITE = DefaultConfig(
    TITLE = "Title in default",
    DESC = "Desc in default", 
    ENGINES = ['blog', ]
)

BLOG = DefaultConfig(
    URL = "blog",
    PERMALINK = "{%Y}/{%m}/{%d}/{slug}",
    AUTHOR = "",
    POSTS_PER_PAGE = 10,
    EXCERPT_LENGTH = 50,
    CONTENT_DIR = join(VOLT.CONTENT_DIR, "blog"),
    SINGLE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "post.html"),
    MULTIPlE_TEMPLATE_FILE = join(VOLT.TEMPLATE_DIR, "pagination.html"),
    SORT = ('date', 'title', 'category', 'author', ),
    REQUIRED = ('title', 'time', ),
)
