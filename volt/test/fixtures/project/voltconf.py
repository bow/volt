# Volt default configurations file fixture

import os

from volt.config.base import Config


VOLT = Config(
    CUSTOM_DIR = "custom_dir_user",
)

SITE = Config(
    TITLE = "Title in user",
    ENGINES = ['blog'],
)

BLOG = Config(
    CUSTOM_DIR = os.path.join(VOLT.CUSTOM_DIR, "user_join"),
)
