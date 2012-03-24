# -*- coding: utf-8 -*-
"""
--------------------------
volt.test.test_engine_core
--------------------------

Tests for volt.engine.core.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os
import sys
import unittest
import warnings
from datetime import datetime

from mock import MagicMock, patch, call

from volt.config import Config
from volt.engine.core import Engine, Page, Unit, Pagination, \
        chain_item_permalinks
from volt.exceptions import ConfigError, EmptyUnitsWarning, \
        PermalinkTemplateError, ContentError
from volt.test import USER_DIR


def make_units_mock():
    # define mock units
    Unitlist_mock = list()
    for i in range(5):
        Unitlist_mock.append(MagicMock(spec=Unit))

    # set unit attributes
    unitlist_attrs = [
            {'id': '1',
             'title': 'Radical Notion',
             'time': datetime(2010, 9, 5, 8, 0),
             'tags': ['arthur', 'eames'],
             'author': 'Smith',
             },
            {'id': '2',
             'title': 'One Simple Idea',
             'time': datetime(2010, 7, 30, 4, 31),
             'author': 'Smith',
             'tags': ['eames', 'arthur'],
             'permalink': '/one',
             },
            {'id': '3',
             'title': 'Dream Within A Dream',
             'time': datetime(1998, 4, 5, 8, 0),
             'author': 'Johnson',
             'tags': ['eames', 'arthur', 'cobb'],
             'permalink': '/dream',
             },
            {'id': '4',
             'title': '528491',
             'time': datetime(2002, 8, 17, 14, 35),
             'author': 'Smith',
             'tags': ['cobb', 'arthur'],
             'permalink': '/528491',
             },
            {'id': '5',
             'title': 'Dream is Collapsing',
             'time': datetime(2011, 9, 5, 8, 0),
             'tags': ['ariadne', 'arthur'],
             'author': 'Johnson',
             },
            ]
    for idx, attr in enumerate(unitlist_attrs):
        for field in attr:
            setattr(Unitlist_mock[idx], field, attr[field])

    return Unitlist_mock


def make_sessionconfig_mock():

    configs = ['VOLT', 'SITE', ]

    VOLT = {'USER_CONF': os.path.join(USER_DIR, 'voltconf.py'),
            'ROOT_DIR': USER_DIR,
            'CONTENT_DIR': os.path.join(USER_DIR, 'content'),
            'TEMPLATE_DIR': os.path.join(USER_DIR, 'templates'),
            'SITE_DIR': os.path.join(USER_DIR, 'site'),
           }
    SITE = {'URL': 'http://foo.com',
           }

    sessionconfig_mock = MagicMock()

    for config in configs:
        setattr(sessionconfig_mock, config, MagicMock())
        for key in eval(config):
            setattr(getattr(sessionconfig_mock, config), key, eval(config)[key])

    return sessionconfig_mock

SessionConfig_mock = make_sessionconfig_mock()


class TestEngineCoreMethods(unittest.TestCase):

    def test_chain_item_permalinks_missing_neighbor_permalink(self):
        units = make_units_mock()
        self.assertRaises(ContentError, chain_item_permalinks, units)

    def test_chain_item_permalinks_ok(self):
        units = make_units_mock()[1:-1]
        assert [unit.id for unit in units] == ['2', '3', '4']
        chain_item_permalinks(units)

        self.assertEqual(units[0].permalink_next, units[1].permalink)
        self.assertFalse(hasattr(units[0], 'permalink_prev'))

        self.assertEqual(units[1].permalink_next, units[2].permalink)
        self.assertEqual(units[1].permalink_prev, units[0].permalink)

        self.assertFalse(hasattr(units[-1], 'permalink_next'))
        self.assertEqual(units[-1].permalink_prev, units[1].permalink)


@patch('volt.engine.core.CONFIG', SessionConfig_mock)
class TestEngine(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()

    def test_create_units(self):
        self.assertRaises(NotImplementedError, self.engine.create_units, )

    def test_activate(self):
        self.assertRaises(NotImplementedError, self.engine.activate, )

    def test_dispatch(self):
        self.assertRaises(NotImplementedError, self.engine.dispatch, )

    def test_prime_user_conf_entry_none(self):
        self.assertRaises(ConfigError, self.engine.prime, )

    def test_prime_content_dir_undefined(self):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'
        self.assertRaises(ConfigError, self.engine.prime, )

    def test_prime_user_conf_not_config(self):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST_BAD'
        self.engine.config.CONTENT_DIR = 'engine_test'
        self.assertRaises(TypeError, self.engine.prime, )

    def test_prime_consolidation(self):
        defaults = Config(
            BAR = 'engine bar in default',
            QUX = 'engine qux in default',
            CONTENT_DIR = 'engine_test',
            UNIT_TEMPLATE = 'template.html',
        )
        self.engine.config = defaults
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'

        self.engine.prime()

        self.assertEqual(self.engine.config.FOO, 'engine foo in user')
        self.assertEqual(self.engine.config.BAR, 'engine bar in user')
        self.assertEqual(self.engine.config.QUX, 'engine qux in default')
        self.assertEqual(self.engine.config.CONTENT_DIR, os.path.join(\
                USER_DIR, 'content', 'engine_test'))
        self.assertEqual(self.engine.config.UNIT_TEMPLATE, os.path.join(\
                USER_DIR, 'templates', 'template.html'))

    def test_sort_units_bad_key(self):
        self.engine.units = make_units_mock()
        self.engine.config.SORT_KEY = 'date'
        self.assertRaises(ContentError, self.engine.sort_units, )

    def test_sort_units_ok(self):
        self.engine.units = make_units_mock()
        self.engine.config.SORT_KEY = '-time'
        titles = ['Dream is Collapsing', 'Radical Notion', 'One Simple Idea', \
                  '528491', 'Dream Within A Dream',]
        self.assertNotEqual([x.title for x in self.engine.units], titles)
        self.engine.sort_units()
        self.assertEqual([x.title for x in self.engine.units], titles)


class TestEnginePaginations(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()
        self.engine.config.URL = 'test'
        self.engine.config.UNITS_PER_PAGINATION = 2

    def test_url_undefined(self):
        del self.engine.config.URL
        self.engine.config.PAGINATIONS = ('',)
        self.assertRaises(ConfigError, self.engine.create_paginations, )

    def test_units_per_pagination_undefined(self):
        del self.engine.config.UNITS_PER_PAGINATION
        self.engine.config.PAGINATIONS = ('',)
        self.assertRaises(ConfigError, self.engine.create_paginations, )

    def test_pagination_patterns_undefined(self):
        self.assertRaises(ConfigError, self.engine.create_paginations, )

    @patch.object(warnings, 'warn')
    def test_empty_units_warning(self, warn_mock):
        self.engine.config.PAGINATIONS = ('',)
        self.engine.create_paginations()
        args = [call('Engine has no units to paginate.', EmptyUnitsWarning)]
        self.assertEqual(warn_mock.call_args_list, args)

    def test_bad_pagination_pattern(self):
        self.engine.units = make_units_mock()
        self.engine.config.PAGINATIONS = ('{bad}/pattern',)
        self.assertRaises(PermalinkTemplateError, \
                self.engine.create_paginations, )

    def test_paginate_not_implemented(self):
        self.engine.units = make_units_mock()
        self.engine.config.PAGINATIONS = ('unimplemented/{newtype}',)
        for unit in self.engine.units:
            setattr(unit, 'newtype', dict(foo='bar'))
        self.assertRaises(NotImplementedError, self.engine.create_paginations, )

    @patch('volt.engine.core.Pagination')
    def test_create_paginations_ok(self, Pagination_mock):
        self.engine.units = make_units_mock()
        pagination_patterns = ('',
                               'tag/{tags}',
                               'author/{author}',
                               '{time:%Y}',
                               '{time:%Y/%m}',)
        expected = ['',
                    'tag/arthur', 'tag/eames', 'tag/ariadne', 'tag/cobb',
                    'author/Smith', 'author/Johnson',
                    '2011', '2010', '2002', '1998',
                    '2011/09', '2010/09', '2010/07', '2002/08', '1998/04',]

        self.engine.config.PAGINATIONS = pagination_patterns
        pagins = self.engine.create_paginations()
        observed = sum([len(x) for x in pagins.values()])
        self.assertEqual(observed, len(expected))

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_all(self, paginator_mock):
        self.engine.units = make_units_mock()
        base_permalist = ['test']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_all(field, base_permalist, 2)]

        self.assertEqual(paginator_mock.call_count, 1)
        expected = call(self.engine.units, ['test'], 2)
        self.assertEqual(paginator_mock.call_args, expected)

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_single(self, paginator_mock):
        self.engine.units = make_units_mock()
        base_permalist = ['test', 'author', '{author}']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_single(field, base_permalist, 2)]

        self.assertEqual(2, paginator_mock.call_count)
        call1 = call(self.engine.units[:2] + [self.engine.units[3]], \
                ['test', 'author', 'Smith'], 2)
        call2 = call([self.engine.units[2], self.engine.units[4]], \
                ['test', 'author', 'Johnson'], 2)
        paginator_mock.assert_has_calls([call1, call2], any_order=True)

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_multiple(self, paginator_mock):
        self.engine.units = make_units_mock()
        base_permalist = ['test', 'tag', '{tags}']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_multiple(field, base_permalist, 2)]

        self.assertEqual(4, paginator_mock.call_count)
        call1 = call([self.engine.units[4]], ['test', 'tag', 'ariadne'], 2)
        call2 = call(self.engine.units[2:4], ['test', 'tag', 'cobb'], 2)
        call3 = call(self.engine.units[:3], ['test', 'tag', 'eames'], 2)
        call4 = call(self.engine.units, ['test', 'tag', 'arthur'], 2)
        paginator_mock.assert_has_calls([call1, call2, call3, call4], any_order=True)

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_datetime_single_time_token(self, paginator_mock):
        self.engine.units = make_units_mock()
        base_permalist = ['test', '{time:%Y}']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_datetime(field, base_permalist, 2)]

        self.assertEqual(4, paginator_mock.call_count)
        call1 = call(self.engine.units[:2], ['test', '2010'], 2)
        call2 = call([self.engine.units[2]], ['test', '1998'], 2)
        call3 = call([self.engine.units[3]], ['test', '2002'], 2)
        call4 = call([self.engine.units[4]], ['test', '2011'], 2)
        paginator_mock.assert_has_calls([call1, call2, call3, call4], any_order=True)

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_datetime_multiple_time_tokens(self, paginator_mock):
        self.engine.units = make_units_mock()
        base_permalist = ['test', '{time:%Y/%m}']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_datetime(field, base_permalist, 2)]

        self.assertEqual(paginator_mock.call_count, 5)
        call1 = call([self.engine.units[0]], ['test', '2010', '09'], 2)
        call2 = call([self.engine.units[1]], ['test', '2010', '07'], 2)
        call3 = call([self.engine.units[2]], ['test', '1998', '04'], 2)
        call4 = call([self.engine.units[3]], ['test', '2002', '08'], 2)
        call5 = call([self.engine.units[4]], ['test', '2011', '09'], 2)
        paginator_mock.assert_has_calls([call1, call2, call3, call4, call5], \
                any_order=True)

    @patch('volt.engine.core.Pagination')
    def test_paginator(self, Pagination_mock):
        self.engine.units = make_units_mock()
        pagins = [p for p in self.engine._paginator(self.engine.units, ['base'], 2)]

        self.assertEqual(3, len(pagins))
        call1 = call(self.engine.units[:2], 0, ['base'])
        call2 = call(self.engine.units[2:4], 1, ['base'])
        call3 = call(self.engine.units[4:], 2, ['base'])
        Pagination_mock.assert_has_calls([call1, call2, call3], any_order=True)


class TestPage(unittest.TestCase):

    def setUp(self):
        self.page = Page()
        self.page.id = 'id'

    def test_repr(self):
        repr = self.page.__repr__()
        self.assertEqual(repr, 'Page(id)')

    def test_slugify_error(self):
        slugify = self.page.slugify
        self.assertRaises(ContentError, slugify, 'Röyksopp - Eple')
        self.assertRaises(ContentError, slugify, '宇多田ヒカル')
        self.assertRaises(ContentError, slugify, '&**%&^%&$-')

    @patch.object(sys, 'version_info', [3])
    def test_slugify_error_py3(self):
        self.test_slugify_error()

    def test_slugify_ok(self):
        self.page.id = 'id'
        slugify = self.page.slugify
        self.assertEqual(slugify('Move along people, this is just a test'),
                'move-along-people-this-is-just-test')
        self.assertEqual(slugify('What does it mean to say !&^#*&@$))*((&?'),
                'what-does-it-mean-to-say')
        self.assertEqual(slugify('What about the A* search algorithm?'),
                'what-about-the-a-search-algorithm')
        self.assertEqual(slugify('--This- is a bad -- -*&( ---___- title---'),
                'this-is-bad-title')
        self.assertEqual(slugify("Hors d'oeuvre, a fully-loaded MP5, and an astronaut from Ann Arbor."),
                'hors-doeuvre-fully-loaded-mp5-and-astronaut-from-ann-arbor')
        self.assertEqual(slugify('Kings of Convenience - Know How (feat. Feist)'),
                'kings-of-convenience-know-how-feat-feist')
        self.assertEqual(slugify('A Journey Through the Himalayan Mountains. Part 1: An Unusual Guest'),
                'journey-through-the-himalayan-mountains-part-1-unusual-guest')

    @patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', True)
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_get_path_and_permalink_index_html_true(self):
        self.page.permalist = ['blog', 'not', 'string']

        path, permalink, permalink_abs = self.page.get_path_and_permalink()

        self.assertEqual(path, os.path.join(USER_DIR, 'site', \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(permalink, '/blog/not/string/')
        self.assertEqual(permalink_abs, 'http://foo.com/blog/not/string')

    @patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', False)
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_get_path_and_permalink_index_html_false(self):
        self.page.permalist = ['blog', 'not', 'string']

        path, permalink, permalink_abs = self.page.get_path_and_permalink()

        self.assertEqual(path, os.path.join(USER_DIR, 'site', \
                'blog', 'not', 'string.html'))
        self.assertEqual(permalink, '/blog/not/string.html')
        self.assertEqual(permalink_abs, 'http://foo.com/blog/not/string.html')


class TestUnit(unittest.TestCase):

    def setUp(self):
        self.unit = Unit('01.md')

    def test_fields(self):
        self.assertEqual(self.unit.fields, ['id'])

    def test_check_required(self):
        req = ('title', 'surprise', )
        self.assertRaises(ContentError, self.unit.check_required, req)

    def test_check_protected(self):
        prot = ('cats', )
        self.assertRaises(ContentError, self.unit.check_protected, 'cats', prot)

    def test_as_list_trailing(self):
        tags = 'ripley, ash, kane   '
        taglist = ['ripley', 'ash', 'kane'].sort()
        self.assertEqual(self.unit.as_list(tags, ', ').sort(), taglist)

    def test_as_list_extra_separator(self):
        tags = 'wickus;christopher;koobus;'
        taglist = ['wickus', 'christopher', 'koobus'].sort()
        self.assertEqual(self.unit.as_list(tags, ';').sort(), taglist)

    def test_as_list_duplicate_item(self):
        tags = 'trinity, twin, twin, morpheus'
        taglist = ['trinity', 'twin', 'morpheus'].sort()
        self.assertEqual(self.unit.as_list(tags, ', ').sort(), taglist)

    def test_get_permalist_error(self):
        self.assertRaises(PermalinkTemplateError, self.unit.get_permalist, \
                'bali/{beach}/party')

    def test_get_permalist_ok(self):
        get_permalist = self.unit.get_permalist
        self.unit.slug = 'yo-dawg'
        self.unit.time = datetime(2009, 1, 28, 16, 47)

        self.assertEqual(get_permalist('{time:%Y/%m/%d}/{slug}'),
                ['', '2009', '01', '28', 'yo-dawg'])
        self.assertEqual(get_permalist('{time:%Y}/mustard/{time:%m}/{slug}/'),
                ['', '2009', 'mustard', '01', 'yo-dawg'])
        self.assertEqual(get_permalist('i/love /mustard'),
                ['', 'i', 'love', 'mustard'])


@patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', True)
class TestPagination(unittest.TestCase):

    def setUp(self):
        self.units = [MagicMock(Spec=Unit)] * 5
        self.site_dir = os.path.join(USER_DIR, 'site')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_init_idx_0(self):
        pagin = Pagination(self.units, 0, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'index.html'))
        self.assertEqual(pagin.permalink, '/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_init_idx_1(self):
        pagin = Pagination(self.units, 1, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'page', '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/page/2/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_init_permalist(self):
        pagin = Pagination(self.units, 1, ['tech'])
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'tech', 'page', '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/tech/page/2/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', '')
    @patch('volt.engine.core.CONFIG', SessionConfig_mock)
    def test_init_pagination_url(self):
        pagin = Pagination(self.units, 1, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/2/')
