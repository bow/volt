import os


class BaseEngine(object):
    # methods for:
    # - parsing resource
    # - constructing path for writing results
    # - constructing urls
    pass


class BaseEngineGroup(object):
    # for combining engines, so posts/pages
    # are aware of each other's metadata
    # lazy load? factories?
    pass
