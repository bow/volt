# -*- coding: utf-8 -*-
"""
---------------------
volt.test.test_config
---------------------

Tests for the volt.config module.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
import unittest
from inspect import ismodule

from volt.config import SessionConfig, ConfigNotFoundError, path_import
from volt.test import INSTALL_DIR, USER_DIR


class TestSessionConfig(unittest.TestCase):

    def setUp(self):
        self.CONFIG = SessionConfig(default_dir=INSTALL_DIR, start_dir=USER_DIR)

    def tearDown(self):
        # destroy default config so default values are reset
        del self.CONFIG._default
        del self.CONFIG

    def test_load(self):
        # test if title is overwritten
        self.assertEqual(self.CONFIG.SITE.TITLE, 'Title in user')
        # test if default conf is preserved
        self.assertEqual(self.CONFIG.SITE.DESC, 'Desc in default')
        # test if user-defined path resolution works
        self.assertEqual(self.CONFIG.VOLT.CUSTOM_DIR, \
                os.path.join(USER_DIR, 'custom_dir_user'))
        # test for different URL possibilities
        self.assertEqual(self.CONFIG.SITE.URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.B_URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.C_URL, '')
        # test for lazy loading flag
        self.assertTrue(self.CONFIG._loaded)

    def test_get_root_dir(self):
        # test if exception is properly raised if dir is not a Volt dir
        self.assertRaises(ConfigNotFoundError, SessionConfig().get_root_dir, INSTALL_DIR)
        # test if root path resolution works properly for all dirs in project dir
        self.assertEqual(self.CONFIG.VOLT.ROOT_DIR, USER_DIR)
        self.assertEqual(self.CONFIG.VOLT.ROOT_DIR, SessionConfig().get_root_dir(\
                os.path.join(USER_DIR, "content")))


class TestConfigBase(unittest.TestCase):

    def test_path_import(self):
        self.assertTrue(ismodule(path_import('in_install', \
                os.path.join(INSTALL_DIR, 'engines'))))
        self.assertTrue(ismodule(path_import('in_both', \
                [os.path.join(x, 'engines') for x in [INSTALL_DIR, USER_DIR]])))
