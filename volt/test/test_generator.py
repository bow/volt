# -*- coding: utf-8 -*-
"""
------------------------
volt.test.test_generator
------------------------

Tests for volt.generator.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import unittest

from mock import patch

from volt.engine.core import Engine
from volt.generator import Site
from volt.plugin.core import Plugin
from volt.test import INSTALL_DIR, make_uniconfig_mock


@patch.object(Site, 'config', make_uniconfig_mock())
class SiteCases(unittest.TestCase):

    def setUp(self):
        self.site = Site()

    @patch('volt.generator.path_import')
    def test_get_processor_unknown_type(self, path_import_mock):
        builtin_engine_name = 'volt.test.fixtures.install_dir.engine.builtins.in_install'
        path_import_mock.return_value = __import__(builtin_engine_name)
        self.assertRaises(AssertionError, self.site.get_processor, \
                'in_install', 'foo', INSTALL_DIR)

    def test_get_processor_unknown_name(self):
        self.assertRaises(ImportError, self.site.get_processor, \
                'foo', 'engines', INSTALL_DIR)

    def test_get_processor_builtin_engine(self):
        returned = self.site.get_processor('in_install', 'engines', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestBuiltinEngine')
        self.assertTrue(issubclass(returned, Engine))

    def test_get_processor_user_engine(self):
        returned = self.site.get_processor('in_user', 'engines', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestUserEngine')
        self.assertTrue(issubclass(returned, Engine))

    def test_get_processor_both_engine(self):
        returned = self.site.get_processor('in_both', 'engines', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestUserEngine')
        self.assertTrue(issubclass(returned, Engine))

    def test_get_processor_builtin_plugin(self):
        returned = self.site.get_processor('in_install', 'plugins', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestBuiltinPlugin')
        self.assertTrue(issubclass(returned, Plugin))

    def test_get_processor_user_plugin(self):
        returned = self.site.get_processor('in_user', 'plugins', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestUserPlugin')
        self.assertTrue(issubclass(returned, Plugin))

    def test_get_processor_both_plugin(self):
        returned = self.site.get_processor('in_both', 'plugins', \
                INSTALL_DIR)
        self.assertEqual(returned.__name__, 'TestUserPlugin')
        self.assertTrue(issubclass(returned, Plugin))
