# -*- coding: utf-8 -*-
"""
----------------
volt.engine.blog
----------------

Volt Blog Engine.

The blog engine takes text files as resources and writes the static files
constituting a simple blog.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


from volt.engine import Engine


__name__ = 'blog'


class BlogEngine(Engine):

    """Engine for processing text files into a blog.

    This engine uses the TextUnit class to represent its resource. Prior to
    writing the output, the TextUnit objects are sorted according to the
    configuration. They are then chained together by adding to each unit
    permalinks that link to the previous and/or next units.

    It also build packs (different combinations of units according to their
    header field) and paginates them according to the settings in voltconf.py

    """

    def activate(self):
        # parse individual post and store the results in self.units
        self.units = self.process_text_units(self.CONFIG.BLOG)
        # sort units
        self.sort_units(self.units, self.CONFIG.BLOG.SORT)
        # add prev and next permalinks so blog posts can link to each other
        self.chain_units(self.units)

    def dispatch(self):
        # build packs
        self.packs = self.build_packs(self.CONFIG.BLOG.PACKS, self.units)
        # write output files
        self.write_units(self.CONFIG.BLOG.UNIT_TEMPLATE_FILE)
        self.write_packs(self.CONFIG.BLOG.PACK_TEMPLATE_FILE)
