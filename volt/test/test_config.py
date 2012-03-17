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
from datetime import datetime
from inspect import getabsfile

from volt.config import SessionConfig, ConfigNotFoundError
from volt.config.default import displaytime
from volt.test import INSTALL_DIR, USER_DIR
from volt.utils import path_import


class TestSessionConfigLoad(unittest.TestCase):

    def setUp(self):
        def get_root_dir_mock(x): return USER_DIR
        self.CONFIG = SessionConfig(default_dir=INSTALL_DIR, start_dir=USER_DIR)
        self.CONFIG.get_root_dir = get_root_dir_mock

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
                'content'))
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


class TestSessionConfigRootDir(unittest.TestCase):

    def setUp(self):
        self.CONFIG = SessionConfig()
        self.CONFIG._default.VOLT.USER_CONF = "voltconf.py"

    def test_get_root_dir_current(self):
        start_dir = USER_DIR
        self.assertEqual(self.CONFIG.get_root_dir(start_dir), USER_DIR)

    def test_get_root_dir_child(self):
        start_dir = os.path.join(USER_DIR, "content", "foo", "bar", "baz")
        self.assertEqual(self.CONFIG.get_root_dir(start_dir), USER_DIR)

    def test_get_root_dir_error(self):
        start_dir = INSTALL_DIR
        self.assertRaises(ConfigNotFoundError, self.CONFIG.get_root_dir, \
                start_dir)


class TestPathImport(unittest.TestCase):

    def test_path_import_string(self):
        path = os.path.join(INSTALL_DIR, 'engine', 'builtins')
        mod = path_import('in_install', path)
        mod_path = os.path.join(INSTALL_DIR, 'engine', 'builtins', 'in_install.py')
        self.assertEqual(getabsfile(mod), mod_path)

    def test_path_import_list(self):
        user_path = os.path.join(USER_DIR, 'engines')
        install_path = os.path.join(INSTALL_DIR, 'engine', 'builtins')
        paths = [user_path, install_path]
        mod = path_import('in_both', paths)
        mod_path = os.path.join(USER_DIR, 'engines', 'in_both.py')
        self.assertEqual(getabsfile(mod), mod_path)


class TestBuiltInJinja2Filters(unittest.TestCase):

    def test_displaytime(self):
        format = "%Y-%m-%d"
        obj = datetime(2009, 10, 5, 3, 1)
        self.assertEqual(displaytime(obj, format), "2009-10-05")
