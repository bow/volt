# -*- coding: utf-8 -*-
"""
------------------
volt.test.test_gen
------------------

Tests for volt.gen.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
import unittest
from inspect import ismodule, getabsfile

from volt.gen import Generator
from volt.test import INSTALL_DIR, USER_DIR


class TestGen(unittest.TestCase):

    def test_get_processor_mod(self):
        gen = Generator()
        # test for exception raising if processor_type unknown
        self.assertRaises(AssertionError, gen.get_processor_mod, \
                'builtin_eng', 'builtin_eng', INSTALL_DIR, USER_DIR)

        # test for engine loading from install dir
        mod = gen.get_processor_mod('in_install', 'engines', INSTALL_DIR,
                USER_DIR)
        self.assertTrue(ismodule(mod))

        # test for loading from user dir
        mod = gen.get_processor_mod('in_user', 'engines', INSTALL_DIR,
                USER_DIR)
        self.assertTrue(ismodule(mod))

        # test for loading if present in both user and install
        mod = gen.get_processor_mod('in_both', 'engines', INSTALL_DIR,
                USER_DIR)
        self.assertEqual(getabsfile(mod), os.path.join(USER_DIR, 'engines', \
                'in_both.py'))
