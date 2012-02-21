# Volt base classes for configuration files


class Config(dict):
    """Container class for storing configuration options.
    """

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self

    def override(self, conf_obj):
        """Overrides options of the current Config object with another one.
        """
        for key in conf_obj.keys():
            self[key] = conf_obj[key]
