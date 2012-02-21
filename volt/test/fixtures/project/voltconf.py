# Volt default configurations file fixture

from volt.config.base import Config


VOLT = Config(
    CONTENT_DIR = "engine_dir_user",
)

SITE = Config(
    TITLE = "Title in user",
)
