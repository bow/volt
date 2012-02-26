#!/usr/bin/env python

# tests for the volt.config module

import os
import unittest

from volt import ConfigError
from volt.config import Session
from volt.config.base import import_conf


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.join(self.test_dir, 'fixtures', 'project')
        self.user_conf = os.path.join(self.project_dir, 'voltconf.py')
        self.default_conf = 'volt.test.fixtures.config.default'
        self.config = Session(default_conf=self.default_conf, \
                start_dir=self.project_dir)

    def tearDown(self):
        # destroy default config so default values are reset
        del self.config._default
        del self.config

    def test_load(self):
        # test if title is overwritten
        self.assertEqual(self.config.SITE.TITLE, 'Title in user')
        # test if default conf is preserved
        self.assertEqual(self.config.SITE.DESC, 'Desc in default')
        # test if user-defined path resolution works
        self.assertEqual(self.config.VOLT.CUSTOM_DIR, \
                os.path.join(self.project_dir, 'custom_dir_user'))
        self.assertEqual(self.config.BLOG.CUSTOM_DIR, \
                os.path.join(self.project_dir, 'custom_dir_user', 'user_join'))
        # test for user-only defined Config
        self.assertEqual(self.config.ADDON.TITLE, 'Only in user')
        # test for different URL possibilities
        self.assertEqual(self.config.SITE.URL, 'http://foo.com')
        self.assertEqual(self.config.SITE.B_URL, 'http://foo.com')
        self.assertEqual(self.config.SITE.C_URL, '')
        # test for lazy loading flag
        self.assertTrue(self.config._loaded)

    def test_get_root(self):
        # test if exception is properly raised
        self.assertRaises(ConfigError, Session().get_root, self.test_dir)
        # test if root path resolution works properly for all dirs in project dir
        self.assertEqual(self.config.root, self.project_dir)
        self.assertEqual(self.config.root, Session().get_root(\
                os.path.join(self.project_dir, "content")))

    def test_import_conf(self):
        # load config first since it's a lazy object
        self.config._load()
        # test for dotted notation import
        self.assertIsNotNone(import_conf(self.default_conf))
        # test for absolute path notation import
        self.assertIsNotNone(import_conf(self.user_conf, True))
        # test if exception is properly raised
        self.assertRaises(ImportError, import_conf, self.user_conf)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
