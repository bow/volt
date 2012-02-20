# Volt default configurations file fixture

from volt.config.base import DefaultConfig


VOLT = DefaultConfig(
    USER_CONF = "voltconf.py",
)

TEST = DefaultConfig(
    TITLE = "Title in default",
    DESC = "Desc in default", 
)
