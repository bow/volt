# Volt blog engine

import os
import re
from datetime import datetime

from volt import ParseError, ContentError
from volt.config import config
from volt.engine.base import BaseEngine, TextUnit, BasePack


__name__ = 'blog'


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """

    def run(self):
        self.process_units()
        self.write_units()
        self.packs = self.process_packs(BasePack, range(len(self.units)))
        self.write_packs()
        return self.units

    def process_units(self):
        """Process the individual blog posts.
        """
        # get absolute paths of content files
        content_dir = self.globdir(self.config.BLOG.CONTENT_DIR, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # set pattern for header delimiter
        header_delim = re.compile(r'^---$', re.MULTILINE)

        # parse each file and fill self.contents with BlogUnit-s
        # also set its URL and absolute file path to be written
        for fname in files:
            self.units.append(BlogUnit(fname, header_delim, self.config.BLOG))
            # paths and permalinks are not set in BlogUnit to facillitate
            # testing; ideally, each xUnit should only be using one Config instance
            self.set_unit_paths(self.units[-1], self.config.VOLT.SITE_DIR)

        # sort the units based on config
        self.sort_units(self.config.BLOG.SORT)

        # and set 'next' and 'prev' urls of each units according to the sort
        # so each blog post can link to the next/previous
        self.chain_units()

    def write_units(self):
        """Writes single blog post into its output file.
        """
        template_file = os.path.basename(self.config.BLOG.UNIT_TEMPLATE_FILE)
        template_env = self.config.SITE.template_env
        template = template_env.get_template(template_file)

        for unit in self.units:
            # warn if files are overwritten
            # this indicates a duplicate post, which could result in
            # unexptected results
            if os.path.exists(unit.path):
                # TODO: find a better exception name
                raise ContentError("'%s' already exists!" % unit.path)
            os.makedirs(os.path.dirname(unit.path))
            with open(unit.path, 'w') as target:
                rendered = template.render(page=unit.__dict__, site=self.config.SITE)
                self.write_output(target, rendered)

    def write_output(self, file_obj, string):
        """Writes string to the open file object.

        Arguments:
        file_obj: open file object
        string: string to write

        This is written to facillitate testing of the calling method.
        """
        file_obj.write(string)

    def process_packs(self, pack_class, unit_idxs):
        """Process groups of blog posts.

        Arguments:
        pack_class: subclass of BasePack used to contain unit objects
        unit_idxs: list or tuple containing the index of self.units to be packed;
            the order of this index determines the order of packing

        Returns a list of BasePack objects, representing the contents of a
            group of units
        """
        packs = []
        units_per_pack = self.config.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_idxs) / units_per_pack + \
                (len(unit_idxs) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                packs.append(pack_class(unit_idxs[start:stop], i, \
                        self.config.VOLT.SITE_DIR, ['blog']))
            else:
                packs.append(pack_class(unit_idxs[start:], i, \
                        self.config.VOLT.SITE_DIR, ['blog'], last=True))

        return packs

    def write_packs(self):
        """Writes multiple blog posts to output file.
        """
        template_file = os.path.basename(self.config.BLOG.PACK_TEMPLATE_FILE)
        template_env = self.config.SITE.template_env
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
                rendered = template.render(page=pack.__dict__, site=self.config.SITE)
                self.write_output(target, rendered)
