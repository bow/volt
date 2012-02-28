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
from volt.engine.base import BasePack
from volt.engine.blog import BlogEngine, BlogUnit
from volt.test.mocks import session_mock, blog_content_dir, project_dir


class TestBlogEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BlogEngine(session_mock)

    def test_process_units(self):
        self.engine.config.BLOG.CONTENT_DIR = os.path.join(\
                self.engine.config.BLOG.CONTENT_DIR, 'engine_pass')
        self.engine.process_units()

        self.assertEqual(len(self.engine.units), 5)
        for unit in self.engine.units:
            self.assertTrue(hasattr(unit, 'path'))
            self.assertTrue(hasattr(unit, 'permalink'))

            if self.engine.units.index(unit) == 0:
                self.assertRaises(AttributeError, getattr, unit, 'permalink_prev')
                self.assertEqual('/blog/2010/09/30/one-simple-idea/', unit.permalink_next)
            elif self.engine.units.index(unit) == 4:
                self.assertEqual('/blog/2002/08/17/528491/', unit.permalink_prev)
                self.assertRaises(AttributeError, getattr, unit, 'permalink_next')
            else:
                self.assertTrue(hasattr(unit, 'permalink_prev'))
                self.assertTrue(hasattr(unit, 'permalink_next'))

    def test_process_packs(self):
        self.engine.config.BLOG.POSTS_PER_PAGE = 3
        packs = self.engine.process_packs(BasePack, range(10))
        self.assertEqual(len(packs), 4)
        for pack in packs:
            if packs.index(pack) != 3:
                self.assertEqual(len(pack.unit_idxs), 3)
            else:
                self.assertEqual(len(pack.unit_idxs), 1)

        self.engine.config.BLOG.POSTS_PER_PAGE = 10
        packs = self.engine.process_packs(BasePack, range(3))
        self.assertEqual(len(packs), 1)
        for pack in packs:
            self.assertEqual(len(pack.unit_idxs), 3)




class TestBlogUnit(unittest.TestCase):

    def setUp(self):
        self.config = session_mock.BLOG
        self.content_dir = blog_content_dir
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
