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

from volt.config import SessionConfig, ConfigNotFoundError
from volt.config.base import import_conf
from volt.test import TEST_DIR, PROJECT_DIR


class TestSessionConfig(unittest.TestCase):

    def setUp(self):
        self.user_conf = os.path.join(PROJECT_DIR, 'voltconf.py')
        self.default_conf = 'volt.test.fixtures.config.default'
        self.CONFIG = SessionConfig(default_conf=self.default_conf, \
                start_dir=PROJECT_DIR)

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
                os.path.join(PROJECT_DIR, 'custom_dir_user'))
        self.assertEqual(self.CONFIG.BLOG.CUSTOM_DIR, \
                os.path.join(PROJECT_DIR, 'custom_dir_user', 'user_join'))
        # test for user-only defined Config
        self.assertEqual(self.CONFIG.ADDON.TITLE, 'Only in user')
        # test for different URL possibilities
        self.assertEqual(self.CONFIG.SITE.URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.B_URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.C_URL, '')
        # test for lazy loading flag
        self.assertTrue(self.CONFIG._loaded)

    def test_get_root_dir(self):
        # test if exception is properly raised if dir is not a Volt dir
        self.assertRaises(ConfigNotFoundError, SessionConfig().get_root_dir, TEST_DIR)
        # test if root path resolution works properly for all dirs in project dir
        self.assertEqual(self.CONFIG.VOLT.ROOT_DIR, PROJECT_DIR)
        self.assertEqual(self.CONFIG.VOLT.ROOT_DIR, SessionConfig().get_root_dir(\
                os.path.join(PROJECT_DIR, "content")))

    def test_import_conf(self):
        # load config first since it's a lazy object
        self.CONFIG._load()
        # test for dotted notation import
        self.assertIsNotNone(import_conf(self.default_conf))
        # test for absolute path notation import
        self.assertIsNotNone(import_conf(self.user_conf, True))
        # test if exception is properly raised
        self.assertRaises(ImportError, import_conf, self.user_conf)

    def test_set_plugin_defaults(self):
        default_args = {"BAR" : "baz", "QUX": "qux"}
        # check if PLUGINS is loaded correctly from user conf
        self.assertEqual(self.CONFIG.PLUGINS.FOO, "foo")
        self.assertEqual(self.CONFIG.PLUGINS.BAR, "bar")
        self.CONFIG.set_plugin_defaults(default_args)
        # check plugin values after function is run
        self.assertEqual(self.CONFIG.PLUGINS.FOO, "foo")
        # declared items should not be changed
        self.assertEqual(self.CONFIG.PLUGINS.BAR, "bar")
        # items previously undeclared should be added
        self.assertEqual(self.CONFIG.PLUGINS.QUX, "qux")
