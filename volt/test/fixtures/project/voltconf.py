# Volt default configurations file fixture

import os

from volt.config.base import Config


VOLT = Config(
    CUSTOM_DIR = "custom_dir_user",
)

SITE = Config(
    TITLE = "Title in user",
    ENGINES = ['blog'],
    A_URL = 'http://foo.com',
    B_URL = 'http://foo.com/',
    C_URL = '/',
)

BLOG = Config(
    CUSTOM_DIR = os.path.join(VOLT.CUSTOM_DIR, "user_join"),
)

ADDON = Config(
    TITLE = "Only in user",
)
