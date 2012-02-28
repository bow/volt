# Volt blog engine

import os
import re
from datetime import datetime

from volt import ParseError, ContentError
from volt.config import config
from volt.engine.base import BaseEngine, BaseUnit, BasePack, MARKUP
from volt.util import markupify


__name__ = 'blog'


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """

    def run(self):
        self.process_units()
        self.write_units()
        self.process_packs(range(len(self.units)))
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
        reversed = ('-' == self.config.BLOG.SORT[0])
        sort_key = self.config.BLOG.SORT.strip('-')
        self.units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)

        # and set 'next' and 'prev' urls of each units according to the sort
        # so each blog post can link to the next/previous
        for i in range(len(self.units)):
            if i != 0:
                setattr(self.units[i], 'permalink_prev', self.units[i-1].permalink)
            if i != len(self.units)-1:
                setattr(self.units[i], 'permalink_next', self.units[i+1].permalink)

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

    def process_packs(self, unit_idxs):
        """Process groups of blog posts.

        unit_idxs: list or tuple containing the index of self.units to be packed;
            the order of this index determines the order of packing
        """
        units_per_pack = self.config.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_idxs) / units_per_pack + \
                (len(unit_idxs) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                self.packs.append(BlogPack(unit_idxs[start:stop], i, \
                        self.config.VOLT.SITE_DIR, ['blog']))
            else:
                self.packs.append(BlogPack(unit_idxs[start:], i, \
                        self.config.VOLT.SITE_DIR, ['blog'], last=True))

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

class BlogUnit(BaseUnit):
    """Class representation of a single blog post.
    """
    
    def __init__(self, fname, header_delim, conf):
        """Initializes BlogUnit.

        Arguments:
        fname: blog post filename
        header_delim: compiled regex pattern for header parsing
        conf: Config object containing blog options
        """
        super(BlogUnit, self).__init__(fname)

        with self.open_text(self.id) as source:
            # open file and remove whitespaces
            read = filter(None, header_delim.split(source.read()))

            # header should be parsed by yaml into dict
            header = self.parse_yaml(read.pop(0))
            if not isinstance(header, dict):
                raise ParseError("Header format unrecognizable in '%s'." \
                        % fname)

            # set blog unit file contents as attributes
            for field in header:
                self.check_protected(field, conf.PROTECTED)
                if field in conf.FIELDS_AS_DATETIME:
                    header[field] = self.as_datetime(\
                            header[field], conf.CONTENT_DATETIME_FORMAT)
                if field in conf.FIELDS_AS_LIST:
                    header[field] = self.as_list(header[field], conf.LIST_SEP)
                if field == 'slug':
                    header[field] = self.slugify(header[field])
                if isinstance(header[field], (int, float)):
                    header[field] = str(header[field])
                setattr(self, field.lower(), header[field])

            self.set_markup(MARKUP)
            # content is everything else after header
            self.content = markupify(read.pop(0).strip(), self.markup)

        # check if all required fields are present
        self.check_required(conf.REQUIRED)

        # set other attributes
        # if slug is not set in header, set it now
        if not hasattr(self, 'slug'):
            self.slug = self.slugify(self.title)
        # and set global values
        for field in conf.GLOBAL_FIELDS:
            if not hasattr(self, field):
                setattr(self, field, conf.GLOBAL_FIELDS[field])
        # set displayed time string
        self.display_time = self.time.strftime(conf.DISPLAY_DATETIME_FORMAT)
        # set permalink components
        self.permalist = self.get_permalist(conf.PERMALINK, conf.URL)


class BlogPack(BasePack):

    def __init__(self, unit_idxs, pack_idx, base_dir, base_permalist=[''], \
            base_url='', last=False, pagination_dir=''):
        """Initializes BlogPack instance.

        Arguments:
        unit_idxs: list or tuple containing the indexes of BlogEngine.units
            to write. Packs are made according to unit_idxs' sorting order
        pack_idx: index of the pack object relative to to other pack objects.
        base_dir: absolute file path to the output directory
        base_permalist: list of URL components common to all pack permalinks;
        base_url: base url to be set for the permalink; defaults to '' so
            permalinks are relative
        last: boolean indicating whether this pack is the last one
        pagination_dir: directory for paginated items with index > 1
        """
        self.unit_idxs = unit_idxs
        # because page are 1-indexed and lists are 0-indexed
        self.pack_idx = pack_idx + 1
        # this will be appended for pack_idx > 1, e.g. .../page/2
        self.pagination_dir = pagination_dir

        if self.pack_idx == 1:
            # if it's the first pack page, use base_permalist only
            self.permalist = base_permalist
        else:
            # otherwise add pagination dir and pack index
            self.permalist = base_permalist + [self.pagination_dir, \
                    str(self.pack_idx)]

        # path is path to folder + index.html
        path = [base_dir] + self.permalist + ['index.html']
        self.path = os.path.join(*(path))

        url = [base_url] + self.permalist
        self.permalink = '/'.join(url)

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        pagination_url = [base_url] + base_permalist
        # next permalinks
        if not last:
            self.permalink_next = '/'.join(pagination_url + filter(None, \
                    [self.pagination_dir, str(self.pack_idx + 1)])) + '/'
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(pagination_url) + '/'
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(pagination_url + filter(None, \
                    [self.pagination_dir, str(self.pack_idx - 1)])) + '/'
