# -*- coding: utf-8 -*-
"""
    volt.site
    ~~~~~~~~~

    Site-level functions and classes.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>


class Site(object):

    """Representation of the static site."""

    def __init__(self, session_config):
        self.session_config = session_config
        self.engines = []

    def build(self):
        engines = []
        for econf in self.session_config.engines:
            engine = econf.cls(econf)
            engines.append(engine)
        self.engines = engines

    def build_root(self):
        pass
