# Volt blog engine

from volt.engine.base import BaseEngine, BaseItem


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """
    def run(self):
        print self.__class__.__name__, "activated!"
        print self.config


class BlogItem(BaseItem):
    """Class representation of a single blog post.
    """
    pass
