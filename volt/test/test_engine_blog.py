#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.engine

import glob
import os
import re
import unittest
from datetime import datetime

from volt import ContentError, ParseError
from volt.config import Session
from volt.engine.blog import BlogEngine, BlogUnit


class TestBlogEngine(unittest.TestCase):

    def setUp(self):
        # set up dirs and Session
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.content_dir = os.path.join(self.project_dir, 'content', 'blog', 'engine_pass')
        default_conf = 'volt.test.fixtures.config.default'
        self.conf = Session(default_conf, self.project_dir)
        self.engine = BlogEngine(BlogUnit)

    def test_process_units(self):
        self.engine.process_units(self.content_dir, self.conf)


class TestBlogUnit(unittest.TestCase):

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
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '*'))[0]
        unit_obj = BlogUnit(fname, self.delim, self.config)
        self.assertEqual(unit_obj.id, fname)
        self.assertEqual(unit_obj.time, datetime(2004, 3, 13, 22, 10))
        self.assertEqual(unit_obj.title, '3.14159265')
        self.assertEqual(unit_obj.extra, 'ice cream please')
        self.assertIsNone(unit_obj.empty)
        content = u'<p>Should be parsed correctly.</p>\n\n<p>Hey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434</p>'
        self.assertEqual(unit_obj.content, content)
        self.assertEqual(unit_obj.slug, 'well-how-about-this')
        self.assertEqual(unit_obj.permalist, ['blog', '2004', '03', '13', 'well-how-about-this'])

    def test_init_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '02*'))[0]
        self.assertRaises(ParseError, BlogUnit, fname, self.delim, self.config)

    def test_init_header_typo(self):
        from yaml import scanner
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '03*'))[0]
        self.assertRaises(scanner.ScannerError, BlogUnit, fname, self.delim, self.config)

    def test_init_markup_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '04*'))[0]
        self.assertEqual(BlogUnit(fname, self.delim, self.config).markup, 'html')

    def test_init_protected_set(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '05*'))[0]
        self.assertRaises(ContentError, BlogUnit, fname, self.delim, self.config)
