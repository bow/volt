#!/usr/bin/env python
# -*- coding: utf8 -*-

# tests for volt.plugin

import unittest

from volt.plugin import Processor


class TestPlugin(unittest.TestCase):

    def test_processor(self):
        self.assertRaises(NotImplementedError, Processor().process, )
