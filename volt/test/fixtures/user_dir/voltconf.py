# Volt default configurations file fixture

from volt.config import Config


VOLT = Config(
    CUSTOM_DIR = "custom_dir_user",
)

SITE = Config(
    TITLE = "Title in user",
    URL = 'http://foo.com',
    ENGINES = ['blog'],
    B_URL = 'http://foo.com/',
    C_URL = '/',
)
