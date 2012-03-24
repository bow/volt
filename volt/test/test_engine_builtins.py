# -*- coding: utf-8 -*-
"""
------------------------------
volt.test.test_engine_builtins
------------------------------

Tests for built-in volt.engine components.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import glob
import os
import unittest
from datetime import datetime

from mock import MagicMock, patch, call

from volt.config import Config
from volt.engine.builtins import TextEngine, TextUnit
from volt.exceptions import ContentError
from volt.test import FIXTURE_DIR


class TestTextEngine(unittest.TestCase):

    @patch('volt.engine.builtins.TextUnit')
    def test_create_units(self, TextUnit_mock):
        engine = TextEngine()
        content_dir = os.path.join(FIXTURE_DIR, 'engines', 'engine_pass')
        engine.config.CONTENT_DIR = content_dir
        fnames = ['01_radical-notion.md', '02_one-simple-idea.md',
                  '03_dream-is-collapsing.md', '04_dream-within-a-dream.md',
                  '05_528491.md']
        abs_fnames = [os.path.join(content_dir, x) for x in fnames]

        call_args = zip(abs_fnames, [engine.config] * len(fnames))
        calls = [call(*x) for x in call_args]

        engine.create_units()
        TextUnit_mock.assert_has_calls(calls, any_order=True)


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

#    def test_init(self):
#        # test if text unit is processed correctly
#        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '*'))[0]
#        TextUnit.set_paths = MagicMock()
#        unit_obj = TextUnit(fname, self.CONFIG)
#        self.assertEqual(unit_obj.id, fname)
#        self.assertEqual(unit_obj.time, datetime(2004, 3, 13, 22, 10))
#        self.assertEqual(unit_obj.title, '3.14159265')
#        self.assertEqual(unit_obj.extra, 'ice cream please')
#        self.assertEqual(unit_obj.empty, None)
#        content = u'Should be parsed correctly.\n\nHey look, unicode: \u042d\u0439, \u0441\u043c\u043e\u0442\u0440\u0438, \u042e\u043d\u0438\u043a\u043e\u0434'
#        self.assertEqual(unit_obj.content, content)
#        self.assertEqual(unit_obj.slug, 'well-how-about-this')
#        self.assertEqual(unit_obj.permalist, ['blog', '2004', '03', '13', 'well-how-about-this'])

    def test_init_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '02*'))[0]
        self.assertRaises(ContentError, TextUnit, fname, self.CONFIG)

    def test_init_header_typo(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '03*'))[0]
        self.assertRaises(ContentError, TextUnit, fname, self.CONFIG)

    def test_init_protected_set(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '05*'))[0]
        self.assertRaises(ContentError, TextUnit, fname, self.CONFIG)
