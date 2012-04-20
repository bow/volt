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

from mock import patch

from volt.config import UnifiedConfig, ConfigNotFoundError
from volt.test import INSTALL_DIR, USER_DIR


def get_root_dir_mock(x, y):
    return USER_DIR


class UnifiedConfigLoadCases(unittest.TestCase):

    @patch('volt.config.DEFAULT_CONF_DIR', INSTALL_DIR)
    @patch.object(UnifiedConfig, 'get_root_dir', get_root_dir_mock)
    def setUp(self):
        self.CONFIG = UnifiedConfig()

    def test_load_consolidation(self):
        # user config overriding
        self.assertEqual(self.CONFIG.SITE.TITLE, 'Title in user')
        # default config preservation
        self.assertEqual(self.CONFIG.SITE.DESC, 'Desc in default')
        # arbitrary user config
        self.assertEqual(self.CONFIG.SITE.CUSTOM_OPT, 'custom_opt_user')
    
    def test_load_dir_resolution(self):
        # default.py dir resolution
        self.assertEqual(self.CONFIG.VOLT.CONTENT_DIR, os.path.join(USER_DIR, \
                'contents'))
        # voltconf.py dir resolution
        self.assertEqual(self.CONFIG.VOLT.TEMPLATE_DIR, os.path.join(USER_DIR, \
                'mytemplates'))

    def test_load_url(self):
        # test for different URL possibilities
        self.assertEqual(self.CONFIG.SITE.A_URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.B_URL, 'http://foo.com')
        self.assertEqual(self.CONFIG.SITE.C_URL, '')
        self.assertEqual(self.CONFIG.SITE.D_URL, '')

    def test_load_root_dir(self):
        self.assertEqual(self.CONFIG.VOLT.ROOT_DIR, USER_DIR)

    def test_load_jinja2_env_default(self):
        self.assertTrue('bar' in self.CONFIG.SITE.TEMPLATE_ENV.filters)

    def test_load_jinja2_env_user(self):
        self.assertEqual(self.CONFIG.SITE.TEMPLATE_ENV.filters['foo'](), \
                "foo in user")


class UnifiedConfigRootDirCases(unittest.TestCase):

    def setUp(self):
        self.get_root_dir = UnifiedConfig.get_root_dir

    def test_get_root_dir_current(self):
        self.assertEqual(self.get_root_dir('voltconf.py', USER_DIR), USER_DIR)

    def test_get_root_dir_child(self):
        start_dir = os.path.join(USER_DIR, "contents", "foo", "bar", "baz")
        self.assertEqual(self.get_root_dir('voltconf.py', start_dir), USER_DIR)

    def test_get_root_dir_error(self):
        os.chdir(INSTALL_DIR)
        self.assertRaises(ConfigNotFoundError, self.get_root_dir, \
                'voltconf.py', INSTALL_DIR)
