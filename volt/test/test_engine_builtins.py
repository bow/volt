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
from volt.test import FIXTURE_DIR
from volt.test.test_engine_core import TestUnit


class TestTextEngine(TextEngine):
    def activate(self): pass
    def dispatch(self): pass

class TestTextUnit(TestUnit, TextUnit): pass


class TextEngineCases(unittest.TestCase):

    @patch('volt.engine.builtins.TextUnit')
    def test_units(self, TextUnit_mock):
        engine = TestTextEngine()
        content_dir = os.path.join(FIXTURE_DIR, 'engines', 'engine_pass')
        engine.config.CONTENT_DIR = content_dir
        fnames = ['01_radical-notion.md', '02_one-simple-idea.md',
                  '03_dream-is-collapsing.md', '04_dream-within-a-dream.md',
                  '05_528491.md']
        abs_fnames = [os.path.join(content_dir, x) for x in fnames]

        call_args = zip(abs_fnames, [engine.config] * len(fnames))
        calls = [call(*x) for x in call_args]

        engine.units
        TextUnit_mock.assert_has_calls(calls, any_order=True)

@patch('volt.engine.core.CONFIG', MagicMock())
class TextUnitCases(unittest.TestCase):

    @patch.object(TestTextUnit, 'check_required', MagicMock())
    @patch.object(TestTextUnit, 'slugify')
    def setUp(self, slugify_mock):
        slugify_mock.return_value = u'3.14159265'
        self.config = MagicMock(spec=Config)
        self.content_dir = os.path.join(FIXTURE_DIR, 'units')

    def test_parse_source_header_missing(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '02*'))[0]
        self.assertRaises(ValueError, TestTextUnit, fname, self.config)

    def test_parse_source_header_typo(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_fail', '03*'))[0]
        self.assertRaises(ValueError, TestTextUnit, fname, self.config)

    def test_parse_source_global_fields_ok(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '01*'))[0]
        self.config.GLOBAL_FIELDS = {'foo': 'bar'}
        unit = TestTextUnit(fname, self.config)
        self.assertEqual(unit.foo, 'bar')

    def test_parse_source_slug_ok(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '01*'))[0]
        unit = TestTextUnit(fname, self.config)
        self.assertEqual(unit.title, u'3.14159265')

    def test_parse_source_ok(self):
        fname = glob.glob(os.path.join(self.content_dir, 'unit_pass', '01*'))[0]
        unit = TestTextUnit(fname, self.config)
        unit.content = u'Should be parsed correctly.\n\n\u042e\u043d\u0438\u043a\u043e\u0434'
