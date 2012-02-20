# Volt base classes for configuration files


class Config(dict):
    """Container class for storing configuration options.
    """
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self

class DefaultConfig(Config):
    """Container class for default configuration options.
    """
    def merge(self, conf_obj):
        for key in conf_obj.keys():
            if key in self:
                self[key] = conf_obj[key]
