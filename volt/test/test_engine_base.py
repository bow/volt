#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.engine.base

import glob
import os
import unittest
from datetime import datetime

from mock import Mock

from volt import ContentError
from volt.config import Session
from volt.engine.base import BaseEngine, BaseUnit, BasePack, MARKUP
from volt.test.mocks import session_mock, project_dir, test_dir


class TestBaseEngine(unittest.TestCase):

    def setUp(self):
        self.content_dir = os.path.join(project_dir, 'content', 'blog', '01')
        self.engine = BaseEngine(session_mock)

    def test_init(self):
        # test if exception is raised if engine is not initialized
        # with a session object
        self.assertRaises(TypeError, BaseEngine.__init__, ) 
    
    def test_globdir(self):
        # test if whole directory globbing for files work
        dir_content = ['01_pass.md', 'mockdir']
        dir_content = [os.path.join(self.content_dir, x) for x in dir_content].sort()
        self.assertEqual(self.engine.globdir(self.content_dir).sort(), dir_content)

    def test_set_unit_paths(self):
        path = test_dir
        url = 'http://alay.com'
        self.unit_mock = Mock(spec=BaseUnit)
        self.unit_mock.permalist = ['blog', 'not', 'string']

        # test for default settings
        self.engine.set_unit_paths(self.unit_mock, path, url)
        self.assertEqual(self.unit_mock.path, os.path.join(path, \
                'blog', 'not', 'string', 'index.html'))
        self.assertEqual(self.unit_mock.permalink, 'http://alay.com/blog/not/string/')

        # test for index_html = False
        self.engine.set_unit_paths(self.unit_mock, path, url, index_html=False)
        self.assertEqual(self.unit_mock.path, os.path.join(path, \
                'blog', 'not', 'string.html'))
        self.assertEqual(self.unit_mock.permalink, 'http://alay.com/blog/not/string.html')

        # test if URL is == '' (if set to '/' in voltconf.py)
        self.engine.set_unit_paths(self.unit_mock, path)
        self.assertEqual(self.unit_mock.permalink, '/blog/not/string/')

        # test if unit.permalist[0] == '/' (if set to '/' in voltconf.py)
        self.unit_mock.permalist = ['', 'not', 'string']
        self.engine.set_unit_paths(self.unit_mock, path, url, os.path.join(path, \
                'not', 'string'))
        self.assertEqual(self.unit_mock.permalink, 'http://alay.com/not/string/')

    def test_process_units(self):
        self.assertRaises(NotImplementedError, self.engine.process_units, )

    def test_process_packs(self):
        self.assertRaises(NotImplementedError, self.engine.process_packs, )

    def test_run(self):
        self.assertRaises(NotImplementedError, self.engine.run, )


class TestBaseUnit(unittest.TestCase):

    def setUp(self):
        self.unit = BaseUnit('01.md')

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

    def test_set_markup(self):
        # test if markup is set correctly
        self.unit.set_markup(MARKUP)
        self.assertEqual(self.unit.markup, 'markdown')
        # test if exception is raised for unlisted markup
        setattr(self.unit, 'markup', 'xml')
        self.assertRaises(ContentError, self.unit.set_markup, MARKUP)

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
        self.assertRaises(ContentError, get_permalist, 'i/love /mustard')
        self.assertRaises(ContentError, get_permalist, 'bali/{beach}/party')
