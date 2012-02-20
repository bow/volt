# Volt default configurations file fixture

import os

from volt.config.base import DefaultConfig


VOLT = DefaultConfig(
    USER_CONF = "voltconf.py",

    CONTENT_DIR = "content",
    TEMPLATE_DIR = "templates",
    SITE_DIR = "site",
)

ENGINE = DefaultConfig(
    TITLE = "Title in default",
    DESC = "Desc in default", 
    CONTENT_DIR = os.path.join(VOLT.CONTENT_DIR, "engine")
)
