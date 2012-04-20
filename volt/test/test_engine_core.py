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
from volt.exceptions import EmptyUnitsWarning
from volt.test import USER_DIR, make_units_mock, make_uniconfig_mock


UniConfig_mock = make_uniconfig_mock()


class TestEngine(Engine):
    def dispatch(self): pass
    @property
    def units(self):
        if not hasattr(self, '_lazy_units'):
            setattr(self, '_lazy_units', make_units_mock())
        return self._lazy_units
    @units.setter
    def units(self, units): self._lazy_units = units

class TestPage(Page):
    @property
    def id(self): return 'test'
    @property
    def permalist(self): return self._lazy_permalist
    @permalist.setter
    def permalist(self, permalist): self._lazy_permalist = permalist

class TestUnit(Unit, TestPage): pass


class EngineCoreMethodsCases(unittest.TestCase):

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


@patch('volt.engine.core.CONFIG', UniConfig_mock)
class EngineCases(unittest.TestCase):

    def setUp(self):
        self.engine = TestEngine()

    def test_dispatch(self):
        class TestEngine(Engine):
            def activate(self): pass
            def units(self): return
        self.assertRaises(TypeError, TestEngine.__init__, )

    def test_units(self):
        class TestEngine(Engine):
            def activate(self): pass
            def dispatch(self): pass
        self.assertRaises(TypeError, TestEngine.__init__, )

    def test_prime_user_conf_entry_none(self):
        self.assertRaises(AttributeError, self.engine.prime, )

    def test_prime_content_dir_undefined(self):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'
        self.assertRaises(AttributeError, self.engine.prime, )

    def test_prime_user_conf_not_config(self):
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST_BAD'
        self.engine.config.CONTENT_DIR = 'engine_test'
        self.assertRaises(TypeError, self.engine.prime, )

    def test_prime_consolidation(self):
        defaults = Config(
            BAR = 'engine bar in default',
            QUX = 'engine qux in default',
            UNIT_TEMPLATE = 'template.html',
            URL = 'test',
            CONTENT_DIR = 'engine_test',
            PERMALINK = '',
        )
        self.engine.config = defaults
        self.engine.USER_CONF_ENTRY = 'ENGINE_TEST'

        self.engine.prime()

        self.assertEqual(self.engine.config.FOO, 'engine foo in user')
        self.assertEqual(self.engine.config.BAR, 'engine bar in user')
        self.assertEqual(self.engine.config.QUX, 'engine qux in default')
        self.assertEqual(self.engine.config.CONTENT_DIR, os.path.join(\
                USER_DIR, 'contents', 'engine_test'))
        self.assertEqual(self.engine.config.UNIT_TEMPLATE, os.path.join(\
                USER_DIR, 'templates', 'template.html'))

    def test_sort_units_bad_key(self):
        self.engine.config.SORT_KEY = 'date'
        self.assertRaises(AttributeError, self.engine.sort_units, )

    def test_sort_units_ok(self):
        self.engine.config.SORT_KEY = '-time'
        titles = ['Dream is Collapsing', 'Radical Notion', 'One Simple Idea', \
                  '528491', 'Dream Within A Dream',]
        self.assertNotEqual([x.title for x in self.engine.units], titles)
        self.engine.sort_units()
        self.assertEqual([x.title for x in self.engine.units], titles)

    @patch('volt.engine.core.write_file')
    def test_write_items_duplicate(self, write_mock):
        template_path = 'item.html'
        units = make_units_mock()[:2]
        units[1].path = units[0].path

        assert units[0].path == units[1].path
        with open(units[1].path, 'w'):
            self.assertRaises(IOError, self.engine._write_items, \
                    units, template_path)
        os.remove(units[1].path)

    @patch('volt.engine.core.write_file')
    def test_write_items_ok(self, write_mock):
        template_path = 'item.html'
        units = make_units_mock()[:2]
        self.engine._write_items(units, template_path)

        if sys.version_info[0] < 3:
            rendered = '\xd1\x8e\xd0\xbd\xd0\xb8\xd0\xba\xd0\xbe\xd0\xb4\xd0\xb0'
        else:
            rendered = 'юникода'

        call1 = call(os.path.join(USER_DIR, '1'), rendered + '|1')
        call2 = call(os.path.join(USER_DIR, '2'), rendered + '|2')
        self.assertEqual([call1, call2], write_mock.call_args_list)


class EnginePaginationCases(unittest.TestCase):

    def setUp(self):
        self.engine = TestEngine()
        self.engine.config.URL = 'test'
        self.engine.config.UNITS_PER_PAGINATION = 2

    def test_url_undefined(self):
        del self.engine.config.URL
        self.engine.config.PAGINATIONS = ('',)
        self.assertRaises(AttributeError, getattr, self.engine, 'paginations')

    def test_units_per_pagination_undefined(self):
        del self.engine.config.UNITS_PER_PAGINATION
        self.engine.config.PAGINATIONS = ('',)
        self.assertRaises(AttributeError, getattr, self.engine, 'paginations')

    def test_pagination_patterns_undefined(self):
        self.assertRaises(AttributeError, getattr, self.engine, 'paginations')

    @patch.object(warnings, 'warn')
    def test_empty_units_warning(self, warn_mock):
        self.engine.units = []
        self.engine.config.PAGINATIONS = ('',)
        getattr(self.engine, 'paginations')
        args = [call('TestEngine has no units to paginate.', EmptyUnitsWarning)]
        self.assertEqual(warn_mock.call_args_list, args)

    def test_bad_pagination_pattern(self):
        self.engine.config.PAGINATIONS = ('{bad}/pattern',)
        self.assertRaises(ValueError, getattr, self.engine, 'paginations')

    def test_paginate_not_implemented(self):
        self.engine.config.PAGINATIONS = ('unimplemented/{newtype}',)
        for unit in self.engine.units:
            setattr(unit, 'newtype', dict(foo='bar'))
        self.assertRaises(KeyError, getattr, self.engine, 'paginations')

    @patch('volt.engine.core.Pagination')
    def test_paginations_ok(self, Pagination_mock):
        pagination_patterns = ('',
                               'tag/{tags}',
                               'author/{author}',
                               '{time:%Y}',
                               '{time:%Y/%m}',)
        expected = ['', '2', '3',
                    'tag/arthur', 'tag/arthur/2', 'tag/arthur/3',
                    'tag/eames', 'tag/eames/2', 'tag/ariadne', 'tag/cobb',
                    'author/Smith', 'author/Smith/2', 'author/Johnson',
                    '2011', '2010', '2002', '1998',
                    '2011/09', '2010/09', '2010/07', '2002/08', '1998/04',]

        self.engine.config.PAGINATIONS = pagination_patterns
        observed = sum([len(x) for x in self.engine.paginations.values()])
        self.assertEqual(observed, len(expected))

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_all(self, paginator_mock):
        base_permalist = ['test']
        field = base_permalist[-1][1:-1]
        [x for x in self.engine._paginate_all(field, base_permalist, 2)]

        self.assertEqual(paginator_mock.call_count, 1)
        expected = call(self.engine.units, ['test'], 2)
        self.assertEqual(paginator_mock.call_args, expected)

    @patch('volt.engine.core.Engine._paginator')
    def test_paginate_single(self, paginator_mock):
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
        pagins = [p for p in self.engine._paginator(self.engine.units, ['base'], 2)]

        self.assertEqual(3, len(pagins))
        call1 = call(self.engine.units[:2], 0, ['base'])
        call2 = call(self.engine.units[2:4], 1, ['base'])
        call3 = call(self.engine.units[4:], 2, ['base'])
        Pagination_mock.assert_has_calls([call1, call2, call3], any_order=True)


class PageCases(unittest.TestCase):

    def setUp(self):
        self.page = TestPage()

    def test_repr(self):
        repr = self.page.__repr__()
        self.assertEqual(repr, 'TestPage(test)')

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_slugify_empty(self):
        slugify = self.page.slugify
        cases = ['宇多田ヒカル', '&**%&^%&$-', u'ßÀœø']
        for case in cases:
            self.assertRaises(ValueError, slugify, case)

    @patch('volt.engine.core.CONFIG')
    def test_slugify_char_map_ok(self, config_mock):
        slugify = self.page.slugify
        setattr(config_mock, 'SITE', Config())
        config_mock.SITE.SLUG_CHAR_MAP = {u'ß': 'ss', u'ø': 'o'}
        self.assertEqual(slugify(u'viel-spaß'), 'viel-spass')
        self.assertEqual(slugify(u'Røyksopp'), 'royksopp')
        self.assertEqual(slugify(u'ßnakeørama'), 'ssnakeorama')

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_slugify_ok(self):
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
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_path_permalinks_index_html_true(self):
        self.page.permalist = ['blog', 'not', 'string']
        self.page.slugify = lambda x: x

        self.assertEqual(self.page.path, os.path.join(USER_DIR, 'site', \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(self.page.permalink, '/blog/not/string/')
        self.assertEqual(self.page.permalink_abs, 'http://foo.com/blog/not/string')

    @patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', False)
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_path_permalinks_index_html_false(self):
        self.page.permalist = ['blog', 'not', 'string']
        self.page.slugify = lambda x: x

        self.assertEqual(self.page.path, os.path.join(USER_DIR, 'site', \
                'blog', 'not', 'string.html'))
        self.assertEqual(self.page.permalink, '/blog/not/string.html')
        self.assertEqual(self.page.permalink_abs, 'http://foo.com/blog/not/string.html')


class UnitCases(unittest.TestCase):

    def setUp(self):
        self.unit = TestUnit(Engine.DEFAULTS)
        self.unit.config.URL = '/'

    def test_init(self):
        self.assertRaises(TypeError, TestUnit.__init__, 'foo')

    def test_check_required(self):
        req = ('title', 'surprise', )
        self.assertRaises(NameError, self.unit.check_required, req)

    def test_check_protected(self):
        prot = ('cats', )
        self.assertRaises(ValueError, self.unit.check_protected, 'cats', prot)

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

    def test_permalist_missing_permalink(self):
        self.unit.config.URL = '/'
        del self.unit.config.PERMALINK
        self.assertRaises(AttributeError, getattr, self.unit, 'permalist')

    def test_permalist_missing_url(self):
        self.unit.config.PERMALINK = 'foo'
        del self.unit.config.URL
        self.assertRaises(AttributeError, getattr, self.unit, 'permalist')

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_permalist_error(self):
        self.unit.config.PERMALINK = 'bali/{beach}/party'
        self.assertRaises(AttributeError, getattr, self.unit, 'permalist')

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_permalist_ok_all_token_is_attrib(self):
        self.unit.slug = 'yo-dawg'
        self.unit.time = datetime(2009, 1, 28, 16, 47)
        self.unit.config.PERMALINK = '{time:%Y/%m/%d}/{slug}'
        self.assertEqual(self.unit.permalist, \
                ['', '2009', '01', '28', 'yo-dawg'])

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_permalist_ok_nonattrib_token(self):
        self.unit.slug = 'yo-dawg'
        self.unit.time = datetime(2009, 1, 28, 16, 47)
        self.unit.config.PERMALINK = '{time:%Y}/mustard/{time:%m}/{slug}/'
        self.assertEqual(self.unit.permalist, \
                ['', '2009', 'mustard', '01', 'yo-dawg'])

    @patch('volt.engine.core.CONFIG', MagicMock())
    def test_permalist_ok_space_in_token(self):
        self.unit.config.PERMALINK = 'i/love /mustard'
        self.assertEqual(self.unit.permalist, \
                ['', 'i', 'love', 'mustard'])


class UnitHeaderCases(unittest.TestCase):

    def setUp(self):
        config = MagicMock(spec=Config)
        config.GLOBAL_FIELDS = {}
        TestUnit.title = 'a'
        self.unit = TestUnit(config)

    def test_parse_header_protected(self):
        header_string = "content: this is a protected field"
        self.unit.config.PROTECTED = ('content', )
        self.assertRaises(ValueError, self.unit.parse_header, header_string)

    @patch.object(TestUnit, 'slugify')
    def test_parse_header_slug(self, slugify_mock):
        slugify_mock.return_value = 'foo-slug'
        header_string = "slug: foo-slug"
        self.unit.parse_header(header_string)
        self.assertEqual(self.unit.slug, 'foo-slug')

    def test_parse_header_as_list(self):
        self.unit.config.FIELDS_AS_LIST = 'tags'
        self.unit.config.LIST_SEP = ', '
        header_string = "tags: foo, bar, baz"
        self.unit.parse_header(header_string)
        expected = ['bar', 'baz', 'foo']
        self.unit.tags.sort()
        self.assertEqual(self.unit.tags, expected)

    def test_parse_header_as_datetime(self):
        self.unit.config.DATETIME_FORMAT = '%Y/%m/%d %H:%M'
        self.unit.config.FIELDS_AS_DATETIME = ('time', )
        header_string = "time: 2004/03/13 22:10"
        self.unit.parse_header(header_string)
        self.assertEqual(self.unit.time, datetime(2004, 3, 13, 22, 10))

    def test_parse_header_extra_field(self):
        header_string = "extra: surprise!"
        self.unit.parse_header(header_string)
        self.assertEqual(self.unit.extra, "surprise!")

    def test_parse_header_empty_field(self):
        header_string = "empty: "
        self.unit.parse_header(header_string)
        self.assertEqual(self.unit.empty, '')

    def test_repr(self):
        self.assertEqual(self.unit.__repr__(), 'TestUnit(test)')


@patch('volt.engine.core.CONFIG.SITE.INDEX_HTML_ONLY', True)
class PaginationCases(unittest.TestCase):

    def setUp(self):
        self.units = [MagicMock(Spec=Unit)] * 5
        self.site_dir = os.path.join(USER_DIR, 'site')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_id(self):
        pagin = Pagination(self.units, 0, )
        self.assertEqual(pagin.id, '/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_init_idx_0(self):
        pagin = Pagination(self.units, 0, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'index.html'))
        self.assertEqual(pagin.permalink, '/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_init_idx_1(self):
        pagin = Pagination(self.units, 1, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'page', '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/page/2/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', 'page')
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_init_permalist(self):
        pagin = Pagination(self.units, 1, ['tech'])
        self.assertEqual(pagin.path, os.path.join(self.site_dir, 'tech', 'page', '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/tech/page/2/')

    @patch('volt.engine.core.CONFIG.SITE.PAGINATION_URL', '')
    @patch('volt.engine.core.CONFIG', UniConfig_mock)
    def test_init_pagination_url(self):
        pagin = Pagination(self.units, 1, )
        self.assertEqual(pagin.path, os.path.join(self.site_dir, '2', 'index.html'))
        self.assertEqual(pagin.permalink, '/2/')
