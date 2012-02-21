# Volt default configurations file fixture

from volt.config.base import Config


VOLT = Config(
    CUSTOM_DIR = "custom_dir_user",
)

SITE = Config(
    TITLE = "Title in user",
    ENGINES = ['blog']
)
