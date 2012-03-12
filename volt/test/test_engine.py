# -*- coding: utf-8 -*-
"""
---------------------
volt.test.test_engine
---------------------

Tests for volt.engine.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


import os
import unittest
from datetime import datetime

from mock import MagicMock, patch, call

from volt.engines import Engine, Pagination
from volt.engines.unit import Unit
from volt.test import USER_DIR, FIXTURE_DIR


class TestEngine(unittest.TestCase):

    def setUp(self):
        self.content_dir = os.path.join(FIXTURE_DIR, 'units', '01')
        self.engine = Engine()

    def test_init(self):
        # test if exception is raised if engine is not initialized
        # with a session object
        self.assertRaises(TypeError, Engine.__init__, ) 
    
    def test_globdir(self):
        # test if whole directory globbing for files work
        dir_content = ['01_pass.md', 'mockdir']
        dir_content = [os.path.join(self.content_dir, x) for x in dir_content].sort()
        self.assertEqual(self.engine.globdir(self.content_dir).sort(), dir_content)

    def test_process_text_units(self):
        content_dir = os.path.join(FIXTURE_DIR, 'engines', 'engine_pass')
        fnames = ['01_radical-notion.md', '02_one-simple-idea.md',
                  '03_dream-is-collapsing.md', '04_dream-within-a-dream.md',
                  '05_528491.md']
        abs_fnames = [os.path.join(content_dir, x) for x in fnames]

        call_args = zip(abs_fnames, [self.engine.config] * len(fnames))
        calls = [call(*x) for x in call_args]

        with patch('volt.engines.TextUnit', mocksignature=True) as TextUnit_Mock:
            self.engine.process_text_units(self.engine.config, content_dir)
            TextUnit_Mock.assert_has_calls(calls, any_order=True)

    def test_build_packs(self):
        # define mock units
        Unitlist_Mock = list()
        for i in range(5):
            Unitlist_Mock.append(MagicMock(spec=Unit))

        # set unit attributes
        unitlist_attrs = [
                {'title': 'Dream is Collapsing',
                 'time': datetime(2011, 9, 5, 8, 0),
                 'author': 'Johnson',
                 'tags': ['cobb', 'ariadne', 'fischer'],},
                {'title': 'One Simple Idea',
                 'time': datetime(2010, 9, 30, 4, 31),
                 'author': 'Smith',
                 'tags': ['cobb', 'eames', 'arthur', 'ariadne', 'yusuf'],},
                {'title': 'Radical Notion',
                 'time': datetime(2010, 9, 5, 8, 0),
                 'author': 'Smith',
                 'tags': ['cobb', 'eames', 'arthur'],},
                {'title': '528491',
                 'time': datetime(2002, 8, 17, 14, 35),
                 'author': 'Smith',
                 'tags': ['eames', 'saito', 'cobb'],},
                {'title': 'Dream Within A Dream',
                 'time': datetime(1998, 4, 5, 8, 0),
                 'author': 'Johnson',
                 'tags': ['fischer', 'saito', 'eames'],},
                ]
        for idx, attr in enumerate(unitlist_attrs):
            for field in attr:
                setattr(Unitlist_Mock[idx], field, attr[field])

        self.engine.units = Unitlist_Mock
        base_url = 'blog'
        units_per_pagination = 2
        index_html_only = True

        pack_patterns = ('',
                         'tag/{tags}',
                         'author/{author}',
                         '{time:%Y}',
                         '{time:%Y/%m}',)
        expected = ['',
                    'tag/arthur', 'tag/eames', 'tag/fischer', 'tag/yusuf',
                    'tag/ariadne', 'tag/cobb', 'tag/saito',
                    'author/Smith', 'author/Johnson',
                    '2011', '2010', '2002', '1998',
                    '2011/09', '2010/09', '2002/08', '1998/04',]

        with patch('volt.engines.Pack', mocksignature=True):
            packs = self.engine.build_packs(pack_patterns, base_url, \
                    units_per_pagination, index_html_only)

        observed = packs.keys()
        expected.sort()
        observed.sort()
        self.assertEqual(observed, expected)

    def test_activate(self):
        self.assertRaises(NotImplementedError, self.engine.activate, )

    def test_dispatch(self):
        self.assertRaises(NotImplementedError, self.engine.dispatch, )


class TestPagination(unittest.TestCase):

    def test_init(self):
        units = [MagicMock(Spec=Unit)] * 10
        pagination_url = ''
        site_dir = os.path.join(USER_DIR, 'site')

        # test for pack_idx = 0
        pack_idx = 0
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'index.html'))
        self.assertEqual(pagination.permalist, [])
        self.assertEqual(pagination.permalink, '/')
        self.assertEqual(pagination.permalink_next, '/2/')
        self.assertFalse(hasattr(pagination, 'permalink_prev'))

        # test for pack_idx = 1
        pack_idx = 1
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['2'])
        self.assertEqual(pagination.permalink, '/2/')
        self.assertEqual(pagination.permalink_next, '/3/')
        self.assertEqual(pagination.permalink_prev, '/')

        # test for pack_idx = 2 and is_last
        pack_idx = 2
        base_permalist = []
        is_last = True
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, '3', 'index.html'))
        self.assertEqual(pagination.permalist, ['3'])
        self.assertEqual(pagination.permalink, '/3/')
        self.assertEqual(pagination.permalink_prev, '/2/')
        self.assertFalse(hasattr(pagination, 'permalink_next'))

        # test for base_permalist
        pack_idx = 1
        base_permalist = ['tech']
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url=pagination_url, site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'tech', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['tech', '2'])
        self.assertEqual(pagination.permalink, '/tech/2/')
        self.assertEqual(pagination.permalink_next, '/tech/3/')
        self.assertEqual(pagination.permalink_prev, '/tech/')

        # test for pagination_url
        pack_idx = 1
        base_permalist = []
        is_last = False
        pagination = Pagination(units, pack_idx, base_permalist, is_last=is_last, \
                pagination_url='page', site_dir=site_dir)
        self.assertEqual(pagination.path, os.path.join(site_dir, 'page', '2', 'index.html'))
        self.assertEqual(pagination.permalist, ['page', '2'])
        self.assertEqual(pagination.permalink, '/page/2/')
        self.assertEqual(pagination.permalink_next, '/page/3/')
        self.assertEqual(pagination.permalink_prev, '/')
