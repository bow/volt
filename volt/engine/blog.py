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
import re

from volt import ContentError
from volt.config import CONFIG
from volt.engine import Engine, _RE_PERMALINK


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
        # pack units
        self.packs = self.build_packs(self.CONFIG.BLOG.PACKS)

    def write(self):
        self.write_units(self.CONFIG.BLOG.UNIT_TEMPLATE_FILE)
        self.write_packs(self.CONFIG.BLOG.PACK_TEMPLATE_FILE)


    def write_packs(self, template_file):

        for pack in self.packs:

            template_file = os.path.basename(template_file)
            template_env = self.CONFIG.SITE.TEMPLATE_ENV
            template = template_env.get_template(template_file)

            for pagination in self.packs[pack].paginations:
                # warn if files are overwritten
                # this indicates a duplicate post, which could result in
                # unexptected results
                if os.path.exists(pagination.path):
                    # TODO: find a better exception name
                    raise ContentError("'%s' already exists!" % pagination.path)
                # !!!
                # this could be dangerous, check later
                try:
                    os.makedirs(os.path.dirname(pagination.path))
                except OSError:
                    pass
                with open(pagination.path, 'w') as target:
                    # since pack object only stores indexes of unit in self.unit
                    # we need to get the actual unit items before writing
                    rendered = template.render(page=pagination.__dict__, site=self.CONFIG.SITE)
                    self.write_output(target, rendered)

    def build_packs(self, pack_list):

        packs = dict()

        for pack in pack_list:

            base_permalist = re.findall(_RE_PERMALINK, pack.strip('/') + '/')
            if base_permalist == []:
                # pagination for all items
                unit_groups = [self.units]
                for units in unit_groups:
                    packs[''] = Pack(units, base_permalist)

            else:
                field_token_idx = [base_permalist.index(token) for token in base_permalist if \
                        token.startswith('{') and token.endswith('}')].pop(0)
                field = base_permalist[field_token_idx][1:-1]

                if ':' in field:
                    field, strftime = field.split(':')
                    # get all the date.strftime tokens in a list
                    date_tokens = strftime.strip('/').split('/')
                    # get all datetime fields from units
                    datetime_per_unit = [getattr(x, field) for x in self.units]
                    # construct set of all datetime combinations in self.units
                    # according to the user's supplied pagination URL
                    # e.g. if URL == '%Y/%m' and there are two units with 2009/10
                    # and one with 2010/03 then
                    # all_items == set([('2009', '10), ('2010', '03'])
                    all_items = set(zip(*[[x.strftime(y) for x in datetime_per_unit] \
                            for y in date_tokens]))

                    for item in all_items:
                        unit_groups = [x for x in self.units if \
                                zip(*[[getattr(x, field).strftime(y)] for y in date_tokens])[0] == item]
                        base_permalist[field_token_idx:] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

                elif isinstance(getattr(self.units[0], field), basestring):
                    all_items = set([getattr(x, field) for x in self.units])
                    for item in all_items:
                        unit_groups = [x for x in self.units if item == getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

                # pagination for all item if field is list or tuple
                elif isinstance(getattr(self.units[0], field), (list, tuple)):
                    # append empty string to pagination URL as placeholder for list item
                    # get item list for each unit
                    item_list_per_unit = (getattr(x, field) for x in self.units)
                    # get unique list item in all units
                    all_items = reduce(set.union, [set(x) for x in item_list_per_unit])
                    # iterate and paginate over each unique list item
                    for item in all_items:
                        unit_groups = [x for x in self.units if item in getattr(x, field)]
                        base_permalist[field_token_idx] = item
                        key = '/'.join(base_permalist)
                        packs[key] = Pack(unit_groups, base_permalist)

        return packs


class Pack(object):
    """Packs are URL sections
    """
    def __init__(self, unit_matches, base_permalist):

        self.paginations = []

        # construct permalist components, relative to blog URL
        base_permalist = filter(None, [CONFIG.BLOG.URL] + base_permalist)

        units_per_pack = CONFIG.BLOG.POSTS_PER_PAGE

        # count how many paginations we need
        pagination = len(unit_matches) / units_per_pack + \
                (len(unit_matches) % units_per_pack != 0)

        # construct pack objects for each pagination page
        for i in range(pagination):
            start = i * units_per_pack
            if i != pagination - 1:
                stop = (i + 1) * units_per_pack
                self.paginations.append(Pagination(unit_matches[start:stop], \
                        i, base_permalist, config=CONFIG))
            else:
                self.paginations.append(Pagination(unit_matches[start:], \
                        i, base_permalist, is_last=True, config=CONFIG))


class Pagination(object):

    """TODO
    """

    def __init__(self, units, pack_idx, base_permalist=[], title='',
            is_last=False, config=CONFIG):
        """Initializes a Pagination instance.

        Args:
            units - List containing units to pack.
            pack_idx - Current pack object index.

        Keyword Args:
            base_permalist - List of URL components common to all pack
                permalinks.
            is_last - Boolean indicating whether this pack is the last one.
            config - SessionConfig instance.

        """
        self.title = title
        self.units = units
        # because page are 1-indexed and lists are 0-indexed
        self.pack_idx = pack_idx + 1
        # this will be appended for pack_idx > 1, e.g. .../page/2
        # precautions for empty string, so double '/'s are not introduced
        base_permalist = filter(None, base_permalist)

        if self.pack_idx == 1:
            # if it's the first pack page, use base_permalist only
            self.permalist = base_permalist
        else:
            # otherwise add pagination dir and pack index
            self.permalist = base_permalist + filter(None, [config.SITE.PAGINATION_URL,\
                    str(self.pack_idx)])

        # path is path to folder + index.html
        path = [config.VOLT.SITE_DIR] + self.permalist + ['index.html']
        self.path = os.path.join(*(path))

        url = [''] + self.permalist
        self.permalink = '/'.join(url) + '/'

        # since we can guess the permalink of next and previous pack objects
        # we can set those attributes here (unlike in units)
        pagination_url = [''] + base_permalist
        # next permalinks
        if not is_last:
            self.permalink_next = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx + 1)])) + '/'
        # prev permalinks
        if self.pack_idx == 2:
            # if pagination is at 2, previous permalink is to 1
            self.permalink_prev = '/'.join(pagination_url) + '/'
        elif self.pack_idx != 1:
            self.permalink_prev = '/'.join(pagination_url + filter(None, \
                    [config.SITE.PAGINATION_URL, str(self.pack_idx - 1)])) + '/'
