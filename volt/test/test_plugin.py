# -*- coding: utf-8 -*-
"""
---------------------
volt.test.test_plugin
---------------------

Tests for the volt.plugin package.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import unittest

from volt.plugin.core import Plugin


class TestPlugin(unittest.TestCase):

    def test_run(self):
        self.assertRaises(TypeError, Plugin.__init__, )
