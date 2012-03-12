# Volt default configurations file fixture

from volt.config import Config


VOLT = Config(
    USER_CONF = 'voltconf.py',
    CONTENT_DIR = 'content',
    TEMPLATE_DIR = 'templates',
    LAYOUT_DIR = 'layout',
    SITE_DIR = 'site',
    IGNORE_PATTERN = str(),
)

SITE = Config(
    TITLE = 'Title in default',
    DESC = 'Desc in default', 
    ENGINES = (),
    PLUGINS = (('',[]),),
    PAGINATION_URL = '',
    INDEX_HTML_ONLY = True,
)

JINJA2_FILTERS = Config()
JINJA2_TESTS = Config()
