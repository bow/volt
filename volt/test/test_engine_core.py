# -*- coding: utf-8 -*-
"""
--------------------------
volt.test.test_engine_core
--------------------------

Tests for volt.engine.core.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from __future__ import with_statement
import os
import unittest
import warnings
from datetime import datetime

from mock import MagicMock, patch, call

from volt.config import Config
from volt.engine.core import Engine, Unit, Pagination
from volt.exceptions import ConfigError, EmptyUnitsWarning, \
        PermalinkTemplateError, HeaderFieldError, ContentError
from volt.test import USER_DIR, TEST_DIR


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


class TestEngineUnits(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()
        self.engine.units = make_units_mock()

    def test_sort_units_ok(self):
        key = '-time'
        titles = ['Dream is Collapsing', 'Radical Notion', 'One Simple Idea', \
                  '528491', 'Dream Within A Dream',]
        self.assertNotEqual([x.title for x in self.engine.units], titles)
        self.engine.sort_units(key)
        self.assertEqual([x.title for x in self.engine.units], titles)

    def test_sort_units_bad_key(self):
        key = 'date'
        self.assertRaises(HeaderFieldError, self.engine.sort_units, key)

    def test_chain_units_missing_neighbor_permalink(self):
        self.assertRaises(ContentError, self.engine.chain_units, )

    def test_chain_units_ok(self):
        self.engine.units = self.engine.units[1:-1]
        assert [unit.id for unit in self.engine.units] == ['2', '3', '4']
        self.engine.chain_units()

        self.assertEqual(self.engine.units[0].permalink_next, \
                self.engine.units[1].permalink)
        self.assertFalse(hasattr(self.engine.units[0], 'permalink_prev'))

        self.assertEqual(self.engine.units[1].permalink_next, \
                self.engine.units[2].permalink)
        self.assertEqual(self.engine.units[1].permalink_prev, \
                self.engine.units[0].permalink)

        self.assertFalse(hasattr(self.engine.units[-1], 'permalink_next'))
        self.assertEqual(self.engine.units[-1].permalink_prev, \
                self.engine.units[1].permalink)


class TestEngine(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()

    def test_prime_user_conf_entry_none(self):
        self.assertRaises(ConfigError, self.engine.prime, )

    def test_prime_content_dir_undefined(self):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'
        self.assertRaises(ConfigError, self.engine.prime, )

    @patch('volt.engine.core.CONFIG')
    def test_prime_user_conf_not_config(self, CONFIG_mock):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST_BAD'
        self.engine.config.CONTENT_DIR = 'engine_test'
        self.assertRaises(TypeError, self.engine.prime, )

    @patch('volt.engine.core.CONFIG')
    def test_prime_consolidation(self, CONFIG_mock):
        defaults = Config(
            BAR = 'engine bar in default',
            QUX = 'engine qux in default',
            CONTENT_DIR = 'engine_test',
            UNIT_TEMPLATE = 'template.html',
        )
        self.engine.config = defaults
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'
        CONFIG_mock.VOLT.USER_CONF = os.path.join(USER_DIR, 'voltconf.py')
        CONFIG_mock.VOLT.ROOT_DIR = USER_DIR
        CONFIG_mock.VOLT.CONTENT_DIR = os.path.join(USER_DIR, 'content')
        CONFIG_mock.VOLT.TEMPLATE_DIR = os.path.join(USER_DIR, 'templates')

        self.engine.prime()

        self.assertEqual(self.engine.config.FOO, 'engine foo in user')
        self.assertEqual(self.engine.config.BAR, 'engine bar in user')
        self.assertEqual(self.engine.config.QUX, 'engine qux in default')
        self.assertEqual(self.engine.config.CONTENT_DIR, os.path.join(\
                USER_DIR, 'content', 'engine_test'))
        self.assertEqual(self.engine.config.UNIT_TEMPLATE, os.path.join(\
                USER_DIR, 'templates', 'template.html'))

    def test_activate(self):
        self.assertRaises(NotImplementedError, self.engine.activate, )

    def test_dispatch(self):
        self.assertRaises(NotImplementedError, self.engine.dispatch, )


class TestEngineBuildPacks(unittest.TestCase):

    def setUp(self):
        self.engine = Engine()
        self.engine.config.URL = 'test'
        self.engine.config.POSTS_PER_PAGE = 2

    def test_url_undefined(self):
        del self.engine.config.URL
        self.assertRaises(ConfigError, self.engine.build_packs, ('',))

    def test_units_per_pagination_undefined(self):
        del self.engine.config.POSTS_PER_PAGE
        self.assertRaises(ConfigError, self.engine.build_packs, ('',))

    @patch.object(warnings, 'warn')
    def test_empty_units_warning(self, warn_mock):
        self.engine.build_packs(('',))
        args = [call('Engine has no units to pack.', EmptyUnitsWarning)]
        self.assertEqual(warn_mock.call_args_list, args)

    def test_bad_pack_pattern(self):
        self.engine.units = make_units_mock()
        self.assertRaises(PermalinkTemplateError, self.engine.build_packs, \
                ('{bad}/pattern',))

    def test_packer_not_implemented(self):
        self.engine.units = make_units_mock()
        for unit in self.engine.units:
            setattr(unit, 'newtype', dict(foo='bar'))
        self.assertRaises(NotImplementedError, self.engine.build_packs, \
                ('unimplemented/{newtype}',))

    def test_packer_all(self):
        self.engine.units = make_units_mock()
        base_permalist = ['test']
        field = base_permalist[-1][1:-1]
        with patch('volt.engine.core.Pack') as Pack_mock:
            [x for x in self.engine._packer_all(field, base_permalist, 2)]

        self.assertEqual(Pack_mock.call_count, 1)
        expected = call(self.engine.units, ['test'], 2)
        self.assertEqual(Pack_mock.call_args, expected)

    def test_packer_single(self):
        self.engine.units = make_units_mock()
        base_permalist = ['test', 'author', '{author}']
        field = base_permalist[-1][1:-1]
        with patch('volt.engine.core.Pack') as Pack_mock:
            [x for x in self.engine._packer_single(field, base_permalist, 2)]

        self.assertEqual(2, Pack_mock.call_count)
        call1 = call(self.engine.units[:2] + [self.engine.units[3]], \
                ['test', 'author', 'Smith'], 2)
        call2 = call([self.engine.units[2], self.engine.units[4]], \
                ['test', 'author', 'Johnson'], 2)
        Pack_mock.assert_has_calls([call1, call2], any_order=True)

    def test_packer_multiple(self):
        self.engine.units = make_units_mock()
        base_permalist = ['test', 'tag', '{tags}']
        field = base_permalist[-1][1:-1]
        with patch('volt.engine.core.Pack') as Pack_mock:
            [x for x in self.engine._packer_multiple(field, base_permalist, 2)]

        self.assertEqual(4, Pack_mock.call_count)
        call1 = call([self.engine.units[4]], ['test', 'tag', 'ariadne'], 2)
        call2 = call(self.engine.units[2:4], ['test', 'tag', 'cobb'], 2)
        call3 = call(self.engine.units[:3], ['test', 'tag', 'eames'], 2)
        call4 = call(self.engine.units, ['test', 'tag', 'arthur'], 2)
        Pack_mock.assert_has_calls([call1, call2, call3, call4], any_order=True)

    def test_packer_datetime_single_time_token(self):
        self.engine.units = make_units_mock()
        base_permalist = ['test', '{time:%Y}']
        field = base_permalist[-1][1:-1]
        with patch('volt.engine.core.Pack') as Pack_mock:
            [x for x in self.engine._packer_datetime(field, base_permalist, 2)]

        self.assertEqual(4, Pack_mock.call_count)
        call1 = call(self.engine.units[:2], ['test', '2010'], 2)
        call2 = call([self.engine.units[2]], ['test', '1998'], 2)
        call3 = call([self.engine.units[3]], ['test', '2002'], 2)
        call4 = call([self.engine.units[4]], ['test', '2011'], 2)
        Pack_mock.assert_has_calls([call1, call2, call3, call4], any_order=True)

    def test_packer_datetime_multiple_time_tokens(self):
        self.engine.units = make_units_mock()
        base_permalist = ['test', '{time:%Y/%m}']
        field = base_permalist[-1][1:-1]
        with patch('volt.engine.core.Pack') as Pack_mock:
            [x for x in self.engine._packer_datetime(field, base_permalist, 2)]

        self.assertEqual(Pack_mock.call_count, 5)
        call1 = call([self.engine.units[0]], ['test', '2010', '09'], 2)
        call2 = call([self.engine.units[1]], ['test', '2010', '07'], 2)
        call3 = call([self.engine.units[2]], ['test', '1998', '04'], 2)
        call4 = call([self.engine.units[3]], ['test', '2002', '08'], 2)
        call5 = call([self.engine.units[4]], ['test', '2011', '09'], 2)
        Pack_mock.assert_has_calls([call1, call2, call3, call4, call5], \
                any_order=True)

    @patch('volt.engine.core.Pack', MagicMock, mocksignature=True)
    def build_packs_ok(self):
        self.engine.units = make_units_mock()
        pack_patterns = ('',
                         'tag/{tags}',
                         'author/{author}',
                         '{time:%Y}',
                         '{time:%Y/%m}',)
        expected = ['',
                    'tag/arthur', 'tag/eames', 'tag/ariadne', 'tag/cobb',
                    'author/Smith', 'author/Johnson',
                    '2011', '2010', '2002', '1998',
                    '2011/09', '2010/09', '2010/07', '2002/08', '1998/04',]

        packs = self.engine.build_packs(pack_patterns)
        self.assertEqual(len(packs), len(expected))


class TestUnit(unittest.TestCase):

    def setUp(self):
        self.unit = Unit('01.md')

    def test_check_required(self):
        # test required fields check
        req = ('title', 'surprise', )
        self.assertRaises(HeaderFieldError, self.unit.check_required, req)

    def test_check_protected(self):
        # test protected fields check
        prot = ('cats', )
        self.assertRaises(HeaderFieldError, self.unit.check_protected, 'cats', prot)

    def test_as_into_list_trailing(self):
        tags = 'ripley, ash, kane   '
        taglist = ['ripley', 'ash', 'kane'].sort()
        self.assertEqual(self.unit.as_list(tags, ', ').sort(), taglist)

    def test_as_into_list_extra_separator(self):
        tags = 'wickus;christopher;koobus;'
        taglist = ['wickus', 'christopher', 'koobus'].sort()
        self.assertEqual(self.unit.as_list(tags, ';').sort(), taglist)

    def test_as_into_list_duplicate_item(self):
        tags = 'trinity, twin, twin, morpheus'
        taglist = ['trinity', 'twin', 'morpheus'].sort()
        self.assertEqual(self.unit.as_list(tags, ', ').sort(), taglist)

    def test_slugify_error(self):
        slugify = self.unit.slugify
        self.assertRaises(ContentError, slugify, 'Röyksopp - Eple')
        self.assertRaises(ContentError, slugify, '宇多田ヒカル')
        self.assertRaises(ContentError, slugify, '&**%&^%&$-')

    def test_slugify_ok(self):
        slugify = self.unit.slugify
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

    @patch('volt.engine.core.CONFIG')
    def test_set_paths_index_html_true(self, CONFIG_mock):
        CONFIG_mock.SITE.URL = 'http://alay.com'
        CONFIG_mock.VOLT.SITE_DIR = base_dir = TEST_DIR
        CONFIG_mock.SITE.INDEX_HTML_ONLY = True
        self.unit.permalist = ['blog', 'not', 'string']

        self.unit.set_paths()
        self.assertEqual(self.unit.path, os.path.join(base_dir, \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(self.unit.permalink, '/blog/not/string/')
        self.assertEqual(self.unit.permalink_abs, 'http://alay.com/blog/not/string')

    @patch('volt.engine.core.CONFIG')
    def test_set_paths_index_html_false(self, CONFIG_mock):
        CONFIG_mock.SITE.URL = 'http://alay.com'
        CONFIG_mock.VOLT.SITE_DIR = base_dir = TEST_DIR
        CONFIG_mock.SITE.INDEX_HTML_ONLY = False
        self.unit.permalist = ['blog', 'not', 'string']

        self.unit.set_paths()
        self.assertEqual(self.unit.path, os.path.join(base_dir, \
                'blog', 'not', 'string.html'))
        self.assertEqual(self.unit.permalink, '/blog/not/string.html')
        self.assertEqual(self.unit.permalink_abs, 'http://alay.com/blog/not/string.html')


@patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', True, create=True)
@patch('volt.engine.core.CONFIG', MagicMock())
class TestPagination(unittest.TestCase):

    def test_init(self):
        units = [MagicMock(Spec=Unit)] * 10
        pagination_url = ''
        site_dir = os.path.join(USER_DIR, 'site')

        # test for pack_idx = 0
        pack_idx = 0
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'index.html'))
        self.assertEqual(pagination.permalist, [])
        self.assertEqual(pagination.permalink, '/')
        self.assertEqual(pagination.permalink_next, '/2/')
        self.assertFalse(hasattr(pagination, 'permalink_prev'))

        # test for pack_idx = 1
        pack_idx = 1
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['2'])
        self.assertEqual(pagination.permalink, '/2/')
        self.assertEqual(pagination.permalink_next, '/3/')
        self.assertEqual(pagination.permalink_prev, '/')

        # test for pack_idx = 2 and is_last
        pack_idx = 2
        base_permalist = []
        is_last = True
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, '3', 'index.html'))
        self.assertEqual(pagination.permalist, ['3'])
        self.assertEqual(pagination.permalink, '/3/')
        self.assertEqual(pagination.permalink_prev, '/2/')
        self.assertFalse(hasattr(pagination, 'permalink_next'))

        # test for base_permalist
        pack_idx = 1
        base_permalist = ['tech']
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'tech', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['tech', '2'])
        self.assertEqual(pagination.permalink, '/tech/2/')
        self.assertEqual(pagination.permalink_next, '/tech/3/')
        self.assertEqual(pagination.permalink_prev, '/tech/')

        # test for pagination_url
        pack_idx = 1
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url='page', site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'page', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['page', '2'])
        self.assertEqual(pagination.permalink, '/page/2/')
        self.assertEqual(pagination.permalink_next, '/page/3/')
        self.assertEqual(pagination.permalink_prev, '/')
