"""The core engines of volt
"""

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

class BlogEngine(BaseEngine):
    pass

class PageEngine(BaseEngine):
    pass

class CollectionEngine(BaseEngine):
    pass
