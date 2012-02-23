#!/usr/bin/env python

# tests for volt.engine

import os
import unittest
from datetime import datetime

from volt import ConfigError, ContentError, ParseError
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

    def test_parse(self):
        # test if blog post is parsed correctly
        content_dir = os.path.join(self.content_dir, '01')
        fname = os.path.join(content_dir, '01_pass.md')
        self.engine.parse(content_dir, self.conf)
        item_obj = self.engine.items[fname]
        # actual tests
        self.assertEqual(item_obj.id, fname)
        self.assertEqual(item_obj.time, datetime(2004, 3, 13, 22, 10))
        self.assertEqual(item_obj.title, 'Jabberwock')
        self.assertEqual(item_obj.extra, 'ice cream please')
        self.assertIsNone(item_obj.empty)
        content = u'Should be parsed correctly.\n\nHey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434'
        self.assertEqual(item_obj.content, content)

    def test_parse_header_missing(self):
        content_dir = os.path.join(self.content_dir, '02')
        self.assertRaises(ParseError, self.engine.parse, content_dir, self.conf)

    def test_parse_header_typo(self):
        from yaml import scanner
        content_dir = os.path.join(self.content_dir, '03')
        self.assertRaises(scanner.ScannerError, self.engine.parse, content_dir, self.conf)

    def test_parse_markup_missing(self):
        content_dir = os.path.join(self.content_dir, '04')
        fname = os.path.join(content_dir, '04_markup-missing.post')
        self.assertRaises(ContentError, self.engine.parse, content_dir, self.conf)
