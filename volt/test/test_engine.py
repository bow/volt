# -*- coding: utf-8 -*-
"""
---------------------
volt.test.test_engine
---------------------

Tests for volt.engine.__init__.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import glob
import os
import unittest
from datetime import datetime

from volt.engine import Engine, Unit, TextUnit, Pagination, \
                        HeaderFieldError, PermalinkTemplateError, \
                        ContentError, ParseError
from volt.test import PROJECT_DIR, TEST_DIR
from volt.test.mocks import SessionConfig_Mock, Unit_Mock, Unitlist_Mock


class TestEngine(unittest.TestCase):

    def setUp(self):
        self.content_dir = os.path.join(PROJECT_DIR, 'content', 'blog', '01')
        self.engine = Engine(SessionConfig_Mock)

    def test_init(self):
        # test if exception is raised if engine is not initialized
        # with a session object
        self.assertRaises(TypeError, Engine.__init__, ) 
    
    def test_globdir(self):
        # test if whole directory globbing for files work
        dir_content = ['01_pass.md', 'mockdir']
        dir_content = [os.path.join(self.content_dir, x) for x in dir_content].sort()
        self.assertEqual(self.engine.globdir(self.content_dir).sort(), dir_content)

    def test_set_unit_paths(self):
        path = TEST_DIR
        Unit_Mock.permalist = ['blog', 'not', 'string']

        # test for default settings
        self.engine.set_unit_paths(Unit_Mock, path)
        self.assertEqual(Unit_Mock.path, os.path.join(path, \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(Unit_Mock.permalink, '/blog/not/string/')
        self.assertEqual(Unit_Mock.permalink_abs, 'http://alay.com/blog/not/string')

        # test for set_index_html = False
        self.engine.set_unit_paths(Unit_Mock, path, index_html_only=False)
        self.assertEqual(Unit_Mock.path, os.path.join(path, \
                'blog', 'not', 'string.html'))
        self.assertEqual(Unit_Mock.permalink, '/blog/not/string.html')
        self.assertEqual(Unit_Mock.permalink_abs, 'http://alay.com/blog/not/string.html')

        # test if unit.permalist[0] == '/' (if set to '/' in voltconf.py)
        Unit_Mock.permalist = ['', 'not', 'string']
        self.engine.set_unit_paths(Unit_Mock, path, os.path.join(path, \
                'not', 'string'))
        self.assertEqual(Unit_Mock.permalink, '/not/string/')

    def test_build_packs(self):
        units = Unitlist_Mock
        pack_patterns = ('',
                         'tag/{tags}',
                         'author/{author}',
                         '{time:%Y}',
                         '{time:%Y/%m}',)
        # test for pack pattern listing all
        packs = self.engine.build_packs(pack_patterns, units)
        self.assertEqual(len(packs), 18)
        # check amount of paginations per pack
        self.assertEqual(len(packs[''].paginations), 3)
        self.assertEqual(len(packs['tag/arthur'].paginations), 1)
        self.assertEqual(len(packs['tag/eames'].paginations), 2)
        self.assertEqual(len(packs['tag/fischer'].paginations), 1)
        self.assertEqual(len(packs['tag/yusuf'].paginations), 1)
        self.assertEqual(len(packs['tag/ariadne'].paginations), 1)
        self.assertEqual(len(packs['tag/cobb'].paginations), 2)
        self.assertEqual(len(packs['tag/saito'].paginations), 1)
        # that's enough ~ now check if all pack patterns are present
        expected = ['', 'tag/arthur', 'tag/eames', 'tag/fischer', 'tag/yusuf',
                    'tag/ariadne', 'tag/cobb', 'tag/saito', '2011', '2010',
                    '2002', '1998', '2011/09', '2010/09', '2002/08', '1998/04',
                    'author/Smith', 'author/Johnson',]
        expected.sort()
        observed = packs.keys()
        observed.sort()
        self.assertEqual(observed, expected)

    def test_activate(self):
        self.assertRaises(NotImplementedError, self.engine.activate, )

    def test_dispatch(self):
        self.assertRaises(NotImplementedError, self.engine.dispatch, )


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

    def test_as_into_list(self):
        # test if specified fields are processed into lists
        tags = 'ripley, ash, kane   '
        taglist = ['ripley', 'ash', 'kane'].sort()
        self.assertEqual(self.unit.as_list(tags, ', ').sort(), taglist)
        cats = 'wickus;christopher;koobus;'
        catlist = ['wickus', 'christopher', 'koobus'].sort()
        self.assertEqual(self.unit.as_list(cats, ';').sort(), catlist)
        grps = 'trinity, twin, twin, morpheus'
        grplist = ['trinity', 'twin', 'morpheus'].sort()
        self.assertEqual(self.unit.as_list(grps, ', ').sort(), grplist)

    def test_slugify(self):
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
        self.assertRaises(ContentError, slugify, 'Röyksopp - Eple')
        self.assertRaises(ContentError, slugify, '宇多田ヒカル')
        self.assertRaises(ContentError, slugify, '&**%&^%&$-')

    def test_get_permalist(self):
        get_permalist = self.unit.get_permalist
        self.unit.slug = 'yo-dawg'
        self.unit.time = datetime(2009, 1, 28, 16, 47)
        self.assertEqual(get_permalist('{time:%Y/%m/%d}/{slug}'),
                ['', '2009', '01', '28', 'yo-dawg'])
        self.assertEqual(get_permalist('{time:%Y}/mustard/{time:%m}/{slug}/'),
                ['', '2009', 'mustard', '01', 'yo-dawg'])
        self.assertEqual(get_permalist('i/love /mustard'),
                ['', 'i', 'love', 'mustard'])
        self.assertRaises(PermalinkTemplateError, get_permalist, 'bali/{beach}/party')


class TestTextUnit(unittest.TestCase):

    def setUp(self):
        # in theory, any engine that uses TextUnit can be used
        # blog is chosen just for convenience
        self.CONFIG = SessionConfig_Mock.BLOG
        self.content_dir = os.path.join(PROJECT_DIR, "content", "blog")

    def test_init(self):
        # test if text unit is processed correctly
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '*'))[0]
        unit_obj = TextUnit(fname, self.CONFIG)
        self.assertEqual(unit_obj.id, fname)
        self.assertEqual(unit_obj.time, datetime(2004, 3, 13, 22, 10))
        self.assertEqual(unit_obj.title, '3.14159265')
        self.assertEqual(unit_obj.extra, 'ice cream please')
        self.assertIsNone(unit_obj.empty)
        content = u'Should be parsed correctly.\n\nHey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434'
        self.assertEqual(unit_obj.content, content)
        self.assertEqual(unit_obj.slug, 'well-how-about-this')
        self.assertEqual(unit_obj.permalist, ['blog', '2004', '03', '13', 'well-how-about-this'])

    def test_init_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '02*'))[0]
        self.assertRaises(ParseError, TextUnit, fname, self.CONFIG)

    def test_init_header_typo(self):
        from yaml import scanner
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '03*'))[0]
        self.assertRaises(scanner.ScannerError, TextUnit, fname, self.CONFIG)

    def test_init_protected_set(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '05*'))[0]
        self.assertRaises(HeaderFieldError, TextUnit, fname, self.CONFIG)


class TestPagination(unittest.TestCase):

    def test_init(self):
        units = [Unit_Mock] * 10
        site_dir = os.path.join(PROJECT_DIR, 'site')

        # test for pack_idx = 0
        pack_idx = 0
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                config=SessionConfig_Mock)
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
                config=SessionConfig_Mock)
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
                config=SessionConfig_Mock)
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
                config=SessionConfig_Mock)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'tech', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['tech', '2'])
        self.assertEqual(pagination.permalink, '/tech/2/')
        self.assertEqual(pagination.permalink_next, '/tech/3/')
        self.assertEqual(pagination.permalink_prev, '/tech/')

        # test for pagination_url
        pack_idx = 1
        base_permalist = []
        is_last = False
        SessionConfig_Mock.SITE.PAGINATION_URL = 'page'
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                config=SessionConfig_Mock)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'page', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['page', '2'])
        self.assertEqual(pagination.permalink, '/page/2/')
        self.assertEqual(pagination.permalink_next, '/page/3/')
        self.assertEqual(pagination.permalink_prev, '/')
