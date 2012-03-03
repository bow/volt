# -*- coding: utf-8 -*-
"""
---------------------
volt.test.test_engine
---------------------

Tests for volt.engine.__init__.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>

"""


import glob
import os
import unittest
from datetime import datetime

from volt import ContentError, ParseError
from volt.engine import Engine, Unit, TextUnit, Pack
from volt.test import PROJECT_DIR, TEST_DIR
from volt.test.mocks import SessionConfig_Mock, Unit_Mock


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
        url = 'http://alay.com'
        Unit_Mock.permalist = ['blog', 'not', 'string']

        # test for default settings
        self.engine.set_unit_paths(Unit_Mock, path, url)
        self.assertEqual(Unit_Mock.path, os.path.join(path, \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(Unit_Mock.permalink, 'http://alay.com/blog/not/string/')

        # test for set_index_html = False
        self.engine.set_unit_paths(Unit_Mock, path, url, set_index_html=False)
        self.assertEqual(Unit_Mock.path, os.path.join(path, \
                'blog', 'not', 'string.html'))
        self.assertEqual(Unit_Mock.permalink, 'http://alay.com/blog/not/string.html')

        # test if URL is == '' (if set to '/' in voltconf.py)
        self.engine.set_unit_paths(Unit_Mock, path)
        self.assertEqual(Unit_Mock.permalink, '/blog/not/string/')

        # test if unit.permalist[0] == '/' (if set to '/' in voltconf.py)
        Unit_Mock.permalist = ['', 'not', 'string']
        self.engine.set_unit_paths(Unit_Mock, path, url, os.path.join(path, \
                'not', 'string'))
        self.assertEqual(Unit_Mock.permalink, 'http://alay.com/not/string/')

    def test_parse(self):
        self.assertRaises(NotImplementedError, self.engine.parse, )

    def test_write(self):
        self.assertRaises(NotImplementedError, self.engine.write, )


class TestUnit(unittest.TestCase):

    def setUp(self):
        self.unit = Unit('01.md')

    def test_check_required(self):
        # test required fields check
        req = ('title', 'surprise', )
        self.assertRaises(ContentError, self.unit.check_required, req)

    def test_check_protected(self):
        # test protected fields check
        prot = ('cats', )
        self.assertRaises(ContentError, self.unit.check_protected, 'cats', prot)

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
        self.assertRaises(ContentError, get_permalist, 'bali/{beach}/party')


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
        self.assertRaises(ContentError, TextUnit, fname, self.CONFIG)


class TestPack(unittest.TestCase):

    def test_init(self):
        unit_idxs = range(10)
        site_dir = PROJECT_DIR

        # test for pack_idx = 0
        pack_idx = 0
        base_permalist = []
        base_url = ''
        last = False
        pagination_dir = ''
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, 'index.html'))
        self.assertEqual(pack.permalist, [])
        self.assertEqual(pack.permalink, '/')
        self.assertEqual(pack.permalink_next, '/2/')
        self.assertFalse(hasattr(pack, 'permalink_prev'))

        # test for pack_idx = 1
        pack_idx = 1
        base_permalist = []
        base_url = ''
        last = False
        pagination_dir = ''
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, '2', 'index.html'))
        self.assertEqual(pack.permalist, ['2'])
        self.assertEqual(pack.permalink, '/2/')
        self.assertEqual(pack.permalink_next, '/3/')
        self.assertEqual(pack.permalink_prev, '/')

        # test for pack_idx = 2 and last
        pack_idx = 2
        base_permalist = []
        base_url = ''
        last = True
        pagination_dir = ''
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, '3', 'index.html'))
        self.assertEqual(pack.permalist, ['3'])
        self.assertEqual(pack.permalink, '/3/')
        self.assertEqual(pack.permalink_prev, '/2/')
        self.assertFalse(hasattr(pack, 'permalink_next'))

        # test for base_permalist
        pack_idx = 1
        base_permalist = ['tech']
        base_url = ''
        last = False
        pagination_dir = ''
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, 'tech', '2', 'index.html'))
        self.assertEqual(pack.permalist, ['tech', '2'])
        self.assertEqual(pack.permalink, '/tech/2/')
        self.assertEqual(pack.permalink_next, '/tech/3/')
        self.assertEqual(pack.permalink_prev, '/tech/')

        # test for base_url
        pack_idx = 1
        base_permalist = ['tech']
        base_url = 'http://foobar.com'
        last = False
        pagination_dir = ''
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, 'tech', '2', 'index.html'))
        self.assertEqual(pack.permalist, ['tech', '2'])
        self.assertEqual(pack.permalink, 'http://foobar.com/tech/2/')
        self.assertEqual(pack.permalink_next, 'http://foobar.com/tech/3/')
        self.assertEqual(pack.permalink_prev, 'http://foobar.com/tech/')

        # test for pagination_dir
        pack_idx = 1
        base_permalist = []
        base_url = ''
        last = False
        pagination_dir = 'page'
        pack = Pack(unit_idxs, pack_idx, site_dir, base_permalist, \
                base_url, last, pagination_dir)
        self.assertEqual(pack.path, os.path.join(PROJECT_DIR, 'page', '2', 'index.html'))
        self.assertEqual(pack.permalist, ['page', '2'])
        self.assertEqual(pack.permalink, '/page/2/')
        self.assertEqual(pack.permalink_next, '/page/3/')
        self.assertEqual(pack.permalink_prev, '/')
