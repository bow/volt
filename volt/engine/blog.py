# Volt blog engine

import os

from volt import ContentError
from volt.engine import BaseEngine, BasePack


__name__ = 'blog'


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """

    def run(self):
        # parse individual post and store the results in self.units
        self.units = self.process_text_units(self.CONFIG.BLOG)
        # sort them according to the option
        self.sort_units(self.units, self.CONFIG.BLOG.SORT)
        # add prev and next permalinks so blog posts can link to each other
        self.chain_units(self.units)
        # write each blog posts according to templae
        self.write_units(self.CONFIG.BLOG.UNIT_TEMPLATE_FILE)
        # pack posts according to option
        self.packs = self.process_packs(BasePack, range(len(self.units)))
        # write packs
        self.write_packs()
        # (return units for other purposes?)
        return self.units

    def process_packs(self, pack_class, unit_idxs):
        """Process groups of blog posts.

        Arguments:
        pack_class: subclass of BasePack used to contain unit objects
        unit_idxs: list or tuple containing the index of self.units to be packed;
            the order of this index determines the order of packing

        Returns a list of BasePack objects, representing the contents of a
            group of units
        """
        # raise exception if pack_class is not BasePack subclass
        if not issubclass(pack_class, BasePack):
            raise TypeError("Pack class must be a subclass of BasePack.")

        packs = []
        units_per_pack = self.CONFIG.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_idxs) / units_per_pack + \
                (len(unit_idxs) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                packs.append(pack_class(unit_idxs[start:stop], i, \
                        self.CONFIG.VOLT.SITE_DIR, ['blog']))
            else:
                packs.append(pack_class(unit_idxs[start:], i, \
                        self.CONFIG.VOLT.SITE_DIR, ['blog'], last=True))

        return packs

    def write_packs(self):
        """Writes multiple blog posts to output file.
        """
        template_file = os.path.basename(self.CONFIG.BLOG.PACK_TEMPLATE_FILE)
        template_env = self.CONFIG.SITE.TEMPLATE_ENV
        template = template_env.get_template(template_file)

        for pack in self.packs:
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
                setattr(pack, 'units', [self.units[x] for x in pack.unit_idxs])
                rendered = template.render(page=pack.__dict__, site=self.CONFIG.SITE)
                self.write_output(target, rendered)
