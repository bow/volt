#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.engine

import glob
import os
import re
import unittest
from datetime import datetime

from volt import ContentError, ParseError
from volt.engine import BasePack, TextUnit
from volt.engine.blog import BlogEngine
from volt.test.mocks import session_mock, blog_content_dir, project_dir


class TestBlogEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BlogEngine(session_mock)

    def test_process_text_units(self):
        self.engine.config.BLOG.CONTENT_DIR = os.path.join(\
                self.engine.config.BLOG.CONTENT_DIR, 'engine_pass')
        self.engine.process_text_units(self.engine.config.BLOG)

        self.assertEqual(len(self.engine.units), 5)
        for unit in self.engine.units:
            self.assertTrue(hasattr(unit, 'path'))
            self.assertTrue(hasattr(unit, 'permalink'))

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

        self.assertRaises(TypeError, self.engine.process_packs, TextUnit, range(5))
