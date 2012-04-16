from volt.config import Config

VOLT = Config(
    USER_CONF = 'voltconf.py',
    USER_WIDGET = 'widgets.py',
    CONTENT_DIR = 'contents',
    ASSET_DIR = 'assets',
    TEMPLATE_DIR = 'templates',
)

SITE = Config(
    TITLE = 'Title in default',
    DESC = 'Desc in default', 
    A_URL = 'http://foo.com',
    B_URL = 'http://foo.com/',
    C_URL = '/',
    D_URL = '',
    FILTERS = ('foo', 'bar'),
    TESTS = (),
)
