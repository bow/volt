#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.engine

import glob
import os
import re
import unittest
from datetime import datetime

from volt import ConfigError, ContentError, ParseError
from volt.config import Session
from volt.engine.base import BaseEngine, BaseItem, MARKUP
from volt.engine.blog import BlogEngine, BlogItem


class TestBaseEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.content_dir = os.path.join(self.test_dir, 'fixtures', 'project', \
                'content', 'blog', '01')

    def test_init(self):
        # test if BaseItem subclass is used to initialize engine
        self.assertRaises(TypeError, BaseEngine.__init__, ) 
    
    def test_globdir(self):
        # test if whole directory globbing for files work
        self.engine = BaseEngine(BaseItem)
        dir_content = ['01_pass.md', 'mockdir']
        dir_content = [os.path.join(self.content_dir, x) for x in dir_content].sort()
        self.assertEqual(self.engine.globdir(self.content_dir).sort(), dir_content)
      

class TestBaseItem(unittest.TestCase):

    def setUp(self):
        header = {'title': 'Logos',
                  'time' : '2004/03/13 22:20',
                  'tags' : 'ripley, ash, kane    ',
                  'cats' : 'wickus;christopher;koobus;',
                 }
        self.item = BaseItem()
        self.item.content = 'Content'
        for field in header:
            setattr(self.item, field, header[field])
        self.item.id = '01.md'

    def test_check_required(self):
        # test required fields check
        req = ('title', 'time', 'surprise', )
        self.assertRaises(ContentError, self.item.check_required, req)

    def test_process_into_list(self):
        # test if specified fields are processed into lists
        tags = ['ripley', 'ash', 'kane']
        self.item.process_into_list(['tags'], ', ')
        self.assertEqual(self.item.tags, tags)
        cats = ['wickus', 'christopher', 'koobus']
        self.item.process_into_list(['cats'], ';')
        self.assertEqual(self.item.cats, cats)

    def test_process_time(self):
        # test time parsing
        fmt = '%Y/%m/%d %H:%M'
        self.item.process_time(fmt)
        time_obj = datetime(2004, 3, 13, 22, 20)
        self.assertEqual(self.item.time, time_obj)

    def test_get_markup(self):
        # test if markup is set correctly
        self.item.get_markup(MARKUP)
        self.assertEqual(self.item.markup, 'markdown')
        # test if exception is raised for unlisted markup
        setattr(self.item, 'markup', 'xml')
        self.assertRaises(ContentError, self.item.get_markup, MARKUP)

    def test_set_slug(self):
        self.item.set_slug('Move along people, this is just a test')
        self.assertEqual(self.item.slug, 'move-along-people-this-is-just-test')
        self.item.set_slug('What does it mean to say !&^#*&@$))*((&?')
        self.assertEqual(self.item.slug, 'what-does-it-mean-to-say')
        self.item.set_slug('What about the A* search algorithm?')
        self.assertEqual(self.item.slug, 'what-about-the-a-search-algorithm')
        self.item.set_slug('--This- is a bad -- -*&( ---___- title---')
        self.assertEqual(self.item.slug, 'this-is-bad-title')
        self.item.set_slug("Hors d'oeuvre, a fully-loaded MP5, and an astronaut from Ann Arbor.")
        self.assertEqual(self.item.slug, 'hors-doeuvre-fully-loaded-mp5-and-astronaut-from-ann-arbor')
        self.item.set_slug('Kings of Convenience - Know How (feat. Feist)')
        self.assertEqual(self.item.slug, 'kings-of-convenience-know-how-feat-feist')
        self.item.set_slug('A Journey Through the Himalayan Mountains. Part 1: An Unusual Guest')
        self.assertEqual(self.item.slug, 'journey-through-the-himalayan-mountains-part-1-unusual-guest')
        self.assertRaises(AssertionError, self.item.set_slug, 'Röyksopp - Eple')
        self.assertRaises(AssertionError, self.item.set_slug, '宇多田ヒカル')
        self.assertRaises(ContentError, self.item.set_slug, '&**%&^%&$-')

    def test_set_permalink(self):
        self.item.set_slug('Yo Dawg!')
        self.item.time = datetime(2009, 1, 28, 16, 47)
        self.item.set_permalink('{time:%Y/%m/%d}/{slug}', '/base')
        self.assertEqual(self.item.permalink, '/base/2009/01/28/yo-dawg')
        self.item.set_permalink('{time:%Y}/mustard/{time:%m}/{slug}')
        self.assertEqual(self.item.permalink, '2009/mustard/01/yo-dawg')
        self.assertRaises(ContentError, self.item.set_permalink, 'bali/{beach}/party')

class TestBlogEngine(unittest.TestCase):

    def setUp(self):
        from volt.config import Session
        # set up dirs and Session
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.content_dir = os.path.join(self.project_dir, 'content', 'blog')
        default_conf = 'volt.test.fixtures.config.default'
        self.conf = Session(default_conf, self.project_dir).BLOG
        self.engine = BlogEngine(BlogItem)

    def tearDown(self):
        del self.engine


class TestBlogItem(unittest.TestCase):

    def setUp(self):
        # set up dirs and Session
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.content_dir = os.path.join(self.project_dir, 'content', 'blog')
        default_conf = 'volt.test.fixtures.config.default'
        self.config = Session(default_conf, self.project_dir).BLOG
        self.delim = re.compile(r'^---$', re.MULTILINE)

    def test_init(self):
        # test if blog post is processed correctly
        fname = glob.glob(os.path.join(self.content_dir, 'pass', '*'))[0]
        item_obj = BlogItem(fname, self.delim, self.config)
        self.assertEqual(item_obj.id, fname)
        self.assertEqual(item_obj.time, datetime(2004, 3, 13, 22, 10))
        self.assertEqual(item_obj.title, 'Jabberwock')
        self.assertEqual(item_obj.extra, 'ice cream please')
        self.assertIsNone(item_obj.empty)
        content = u'Should be parsed correctly.\n\nHey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434'
        self.assertEqual(item_obj.content, content)
        self.assertEqual(item_obj.slug, 'jabberwock')

    def test_init_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '02*'))[0]
        self.assertRaises(ParseError, BlogItem, fname, self.delim, self.config)

    def test_init_header_typo(self):
        from yaml import scanner
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '03*'))[0]
        self.assertRaises(scanner.ScannerError, BlogItem, fname, self.delim, self.config)

    def test_init_markup_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'fail', '04*'))[0]
        self.assertEqual(BlogItem(fname, self.delim, self.config).markup, 'html')

