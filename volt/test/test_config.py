#!/usr/bin/env python

# tests for the volt.config module

import os
import unittest

from volt.config import Session


class TestConfig(unittest.TestCase):

    def setUp(self):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        user_conf = os.path.join(test_dir, 'fixtures/project')
        default_conf = 'volt.test.fixtures.default'
        self.config = Session(default_conf, user_conf)

    def test_config(self):
        # test if title is overwritten
        self.assertEqual(self.config.ENGINE.TITLE, 'Title in user')
        # test if default conf is preserved
        self.assertEqual(self.config.ENGINE.DESC, 'Desc in default')
        # test if absolute path resolution for user-defined engine path works
        self.assertEqual(self.config.ENGINE.CONTENT_DIR, \
                os.path.join(self.config.root, "engine_dir_user"))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
    unittest.TextTestRunner(verbosity=2).run(suite)
