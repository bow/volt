# Volt blog engine

import os
import re
from datetime import datetime

from volt import ParseError, ContentError
from volt.config import config
from volt.engine.base import BaseEngine, BaseUnit, MARKUP
from volt.util import markupify


__name__ = 'blog'


class BlogEngine(BaseEngine):
    """Class for processing raw blog content into blog pages and directories.
    """

    def run(self):
        self.process_units(content_dir=config.BLOG.CONTENT_DIR, conf=config)
        self.write_single_unit(config.BLOG.SINGLE_TEMPLATE_FILE, site_conf=config.SITE)
        return self.units

    def write_single_unit(self, template_file, site_conf):
        """Writes single blog post into its output file.

        template_file: absolute path to template file
        site: Config object with site information
        """
        template_file = os.path.basename(template_file)
        template_env = site_conf.template_env
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
                rendered = template.render(page=unit.__dict__, site=site_conf)
                self.write_output(target, rendered)

    def write_output(self, file_obj, string):
        """Writes string to the open file object.

        Arguments:
        file_obj: open file object
        string: string to write

        This is written to facillitate testing of the calling method.
        """
        file_obj.write(string)

    def process_units(self, content_dir, conf):
        """Process the individual blog posts.

        Arguments:
        content_dir: directory containing files to be parsed
        conf: Config object containing blog options
        """
        # get absolute paths of content files
        content_dir = self.globdir(content_dir, iter=True)
        files = (x for x in content_dir if os.path.isfile(x))

        # set pattern for header delimiter
        header_delim = re.compile(r'^---$', re.MULTILINE)

        # parse each file and fill self.contents with BlogUnit-s
        # also set its URL and absolute file path to be written
        for fname in files:
            self.units.append(self.unit_class(fname, header_delim, conf.BLOG))
            # paths and permalinks are not set in BlogUnit to facillitate
            # testing; ideally, each xUnit should only be using one Config instance
            self.set_unit_paths(self.units[-1], conf.VOLT.SITE_DIR, \
                    conf.SITE.URL)

        # sort the units based on config
        reversed = ('-' == config.BLOG.SORT[0])
        sort_key = config.BLOG.SORT.strip('-')
        self.units.sort(key=lambda x: eval('x.' + sort_key), reverse=reversed)

        # and set 'next' and 'prev' urls of each units according to the sort
        # so each blog post can link to the next/previous
        for i in range(len(self.units)):
            if i == 0:
                setattr(self.units[i], 'permalink_next', self.units[i+1].permalink)
            elif i == len(self.units)-1:
                setattr(self.units[i], 'permalink_prev', self.units[i-1].permalink)
            else:
                setattr(self.units[i], 'permalink_next', self.units[i+1].permalink)
                setattr(self.units[i], 'permalink_prev', self.units[i-1].permalink)


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
        # author as well
        if not hasattr(self, 'author'):
            self.author = conf.AUTHOR
        # set displayed time string
        self.display_time = self.time.strftime(conf.DISPLAY_DATETIME_FORMAT)
        self.permalist = self.get_permalist(conf.PERMALINK, conf.URL)
