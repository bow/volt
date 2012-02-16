class Options(dict):
    """Container class for storing configuration options.
    """
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        # set __dict__ to the dict contents itself
        # enables value access by dot notation
        self.__dict__ = self
