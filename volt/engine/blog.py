# -*- coding: utf-8 -*-
"""
----------------
volt.engine.blog
----------------

Volt Blog Engine.

The blog engine takes text files as resources and writes the static files
constituting a simple blog.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""


import os
from datetime import datetime

from volt import ContentError
from volt.engine import Engine, Pack


__name__ = 'blog'


class BlogEngine(Engine):

    """Engine for processing text files into a blog.

    This engine uses the TextUnit class to represent its resource. Prior to
    writing the output, the TextUnit objects are sorted according to the
    configuration. They are then chained together by adding to each unit
    permalinks that link to the previous and/or next units.

    """

    def parse(self):
        # parse individual post and store the results in self.units
        self.units = self.process_text_units(self.CONFIG.BLOG)
        # sort them according to the option
        self.sort_units(self.units, self.CONFIG.BLOG.SORT)
        # add prev and next permalinks so blog posts can link to each other
        self.chain_units(self.units)

    def write(self):
        # write each blog posts according to templae
        self.write_units(self.CONFIG.BLOG.UNIT_TEMPLATE_FILE)
        # pack posts according to option
        for pagination in self.CONFIG.BLOG.PACKS:
            field = self.CONFIG.BLOG.PACKS[pagination]
            pagination = pagination.strip('/').split('/')

            # pagination for all items
            if not field:
                unit_groups = [self.units]
                for units in unit_groups:
                    self.process_packs(Pack, units, pagination)

            # pagination for all item if field is list or tuple
            elif isinstance(getattr(self.units[0], field), (list, tuple)):
                # append empty string to pagination URL as placeholder for list item
                pagination.append('')
                # get item list for each unit
                item_list_per_unit = (getattr(x, field) for x in self.units)
                # get unique list item in all units
                all_items = (reduce(set.union, [set(x) for x in item_list_per_unit]))
                # iterate and paginate over each unique list item
                for item in all_items:
                    unit_groups = [x for x in self.units if item in getattr(x, field)]
                    pagination[-1] = item
                    self.process_packs(Pack, unit_groups, pagination)

            elif isinstance(getattr(self.units[0], field), datetime):
                # get all the date.strftime tokens in a list
                date_tokens = pagination
                # get all datetime fields from units
                all_datetime = [getattr(x, field) for x in self.units]
                # construct set of all datetime combinations in self.units
                # according to the user's supplied pagination URL
                # e.g. if URL == '%Y/%m' and there are two units with 2009/10
                # and one with 2010/03 then
                # all_items == set([('2009', '10), ('2010', '03'])
                all_items = set(zip(*[[x.strftime(y) for x in all_datetime] \
                        for y in date_tokens]))

                for item in all_items:
                    unit_groups = [x for x in self.units if \
                            zip(*[[getattr(x, 'time').strftime(y)] for y in date_tokens])[0] == item]
                    pagination = list(item)
                    self.process_packs(Pack, unit_groups, pagination)

        # write packs
        #self.write_packs()

    def process_packs(self, pack_class, units, base_permalist=[]):
        """Process groups of blog posts.

        Arguments:
        pack_class: subclass of Pack used to contain unit objects
        units: list or tuple containing the index of self.units to be packed;
            the order of this index determines the order of packing
        base_permalist - ...

        Returns a list of Pack objects, representing the contents of a
            group of units
        """
        # raise exception if pack_class is not Pack subclass
        if not issubclass(pack_class, Pack):
            raise TypeError("Pack class must be a subclass of Pack.")

        # construct permalist components, relative to blog URL
        base_permalist = filter(None, [self.CONFIG.BLOG.URL] + base_permalist)

        packs = []
        units_per_pack = self.CONFIG.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(units) / units_per_pack + \
                (len(units) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                packs.append(pack_class(units[start:stop], i, base_permalist, \
                        config=self.CONFIG))
            else:
                packs.append(pack_class(units[start:], i, base_permalist, \
                        is_last=True, config=self.CONFIG))

        template_file = os.path.basename(self.CONFIG.BLOG.PACK_TEMPLATE_FILE)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for pack in packs:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexptected results
            if os.path.exists(pack.path):
                # TODO: find a better exception name
                raise ContentError("'%s' already exists!" % pack.path)
            # !!!
            # this could be dangerous, check later
            try:
                os.makedirs(os.path.dirname(pack.path))
            except OSError:
                pass
            with open(pack.path, 'w') as target:
                # since pack object only stores indexes of unit in self.unit
                # we need to get the actual unit items before writing
                rendered = template.render(page=pack.__dict__, site=self.CONFIG.SITE)
                self.write_output(target, rendered)
