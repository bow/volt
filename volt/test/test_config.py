#!/usr/bin/env python

# tests for the volt.config module

import os
import unittest

from volt import ConfigError
from volt.config import Session


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        user_conf = os.path.join(self.test_dir, 'fixtures/project')
        default_conf = 'volt.test.fixtures.default'
        self.config = Session(default_conf, user_conf)

    def tearDown(self):
        # destroy default config so default values are reset
        del self.config._default
        del self.config

    def test_load(self):
        # test if title is overwritten
        self.assertEqual(self.config.ENGINE.TITLE, 'Title in user')
        # test if default conf is preserved
        self.assertEqual(self.config.ENGINE.DESC, 'Desc in default')
        # test if absolute path resolution for user-defined engine path works
        self.assertEqual(self.config.ENGINE.CONTENT_DIR, \
                os.path.join(self.config.root, "engine_dir_user"))
        # test for lazy loading flag
        self.assertTrue(self.config._loaded)

    def test_get_root(self):
        # test if exception is properly raised
        self.assertRaises(ConfigError, Session().get_root, self.test_dir)
        # test if root path resolution works properly
        self.assertEqual(self.config.root, os.path.join(self.test_dir, \
                'fixtures/project'))

    def test_import_conf(self):
        # load config first since it's a lazy object
        self.config._load()
        # test for dotted notation import
        self.assertIsNotNone(self.config.import_conf(\
                'volt.test.fixtures.default'))
        # test for absolute path notation import
        self.assertIsNotNone(self.config.import_conf(\
                self.config.VOLT.USER_CONF, True))
        # test if exception is properly raised
        self.assertRaises(ImportError, Session().import_conf, \
                self.config.VOLT.USER_CONF)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
