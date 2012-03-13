from volt.config import Config

VOLT = Config(
    USER_CONF = 'voltconf.py',
    CONTENT_DIR = 'content',
    TEMPLATE_DIR = 'templates',
)

SITE = Config(
    TITLE = 'Title in default',
    DESC = 'Desc in default', 
    A_URL = 'http://foo.com',
    B_URL = 'http://foo.com/',
    C_URL = '/',
    D_URL = '',
)

def default_foo(): return "foo in default"
def default_bar(): pass

JINJA2_FILTERS = Config(
    foo = default_foo,
    bar = default_bar,
)
JINJA2_TESTS = Config()
