# -*- coding: utf-8 -*-
"""
--------------------------
volt.test.test_engine_unit
--------------------------

Tests for volt.engine.unit.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import glob
import os
import unittest
from datetime import datetime

from mock import MagicMock

from volt.config import Config
from volt.engines.unit import Unit, TextUnit, HeaderFieldError, \
                              PermalinkTemplateError, ContentError, ParseError
from volt.test import TEST_DIR, FIXTURE_DIR


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

    def test_set_paths(self):
        base_dir = TEST_DIR
        abs_url = 'http://alay.com'
        self.unit.permalist = ['blog', 'not', 'string']

        # test for default settings
        self.unit.set_paths(base_dir, abs_url, index_html_only=True)
        self.assertEqual(self.unit.path, os.path.join(base_dir, \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(self.unit.permalink, '/blog/not/string/')
        self.assertEqual(self.unit.permalink_abs, 'http://alay.com/blog/not/string')

        # test for set_index_html = False
        self.unit.set_paths(base_dir, abs_url, index_html_only=False)
        self.assertEqual(self.unit.path, os.path.join(base_dir, \
                'blog', 'not', 'string.html'))
        self.assertEqual(self.unit.permalink, '/blog/not/string.html')
        self.assertEqual(self.unit.permalink_abs, 'http://alay.com/blog/not/string.html')


class TestTextUnit(unittest.TestCase):

    def setUp(self):
        # in theory, any engine that uses TextUnit can be used
        # blog is chosen just for convenience

        config = MagicMock(spec=Config)
        opts = {
                'URL': 'blog',
                'PERMALINK': '{time:%Y/%m/%d}/{slug}',
                'CONTENT_DATETIME_FORMAT': '%Y/%m/%d %H:%M',
                'DISPLAY_DATETIME_FORMAT': '%A, %d %B %Y',
                'PROTECTED': ('id', 'content', ),
                'REQUIRED': ('title', 'time', ),
                'FIELDS_AS_DATETIME': ('time', ),
                'FIELDS_AS_LIST': ('tags', 'categories', ),
                'LIST_SEP': ', ',
        }
        for key in opts:
            setattr(config, key, opts[key])

        self.CONFIG = config
        self.content_dir = os.path.join(FIXTURE_DIR, 'units')

    def test_init(self):
        # test if text unit is processed correctly
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '*'))[0]
        TextUnit.set_paths = MagicMock()
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
