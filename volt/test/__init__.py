# -*- coding: utf-8 -*-
"""
---------
volt.test
---------

Common Volt test utilities.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

import os
from datetime import datetime

from mock import MagicMock
from jinja2 import Environment, FileSystemLoader

from volt.engine.core import Unit


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(TEST_DIR, 'fixtures')
USER_DIR = os.path.join(FIXTURE_DIR, 'user_dir')
INSTALL_DIR = os.path.join(FIXTURE_DIR, 'install_dir')


def make_uniconfig_mock():

    configs = ['VOLT', 'SITE', ]

    VOLT = {'USER_CONF': os.path.join(USER_DIR, 'voltconf.py'),
            'ROOT_DIR': USER_DIR,
            'CONTENT_DIR': os.path.join(USER_DIR, 'contents'),
            'TEMPLATE_DIR': os.path.join(USER_DIR, 'templates'),
            'SITE_DIR': os.path.join(USER_DIR, 'site'),
           }
    SITE = {'URL': 'http://foo.com',
            'SLUG_CHAR_MAP': {},
            'PAGINATION_URL': '',
            'TEMPLATE_ENV': Environment(\
                loader=FileSystemLoader(VOLT['TEMPLATE_DIR']))
           }

    uniconfig_mock = MagicMock()

    for config in configs:
        setattr(uniconfig_mock, config, MagicMock())
        for key in eval(config):
            setattr(getattr(uniconfig_mock, config), key, eval(config)[key])

    return uniconfig_mock

def make_units_mock():
    # define mock units
    Unitlist_mock = []
    for i in range(5):
        Unitlist_mock.append(MagicMock(spec=Unit))

    # set unit attributes
    unitlist_attrs = [
            {'id': '1',
             'title': 'Radical Notion',
             'time': datetime(2010, 9, 5, 8, 0),
             'tags': ['arthur', 'eames'],
             'author': 'Smith',
             },
            {'id': '2',
             'title': 'One Simple Idea',
             'time': datetime(2010, 7, 30, 4, 31),
             'author': 'Smith',
             'tags': ['eames', 'arthur'],
             'permalink': '/one',
             },
            {'id': '3',
             'title': 'Dream Within A Dream',
             'time': datetime(1998, 4, 5, 8, 0),
             'author': 'Johnson',
             'tags': ['eames', 'arthur', 'cobb'],
             'permalink': '/dream',
             },
            {'id': '4',
             'title': '528491',
             'time': datetime(2002, 8, 17, 14, 35),
             'author': 'Smith',
             'tags': ['cobb', 'arthur'],
             'permalink': '/528491',
             },
            {'id': '5',
             'title': 'Dream is Collapsing',
             'time': datetime(2011, 9, 5, 8, 0),
             'tags': ['ariadne', 'arthur'],
             'author': 'Johnson',
             },
            ]
    for idx, attr in enumerate(unitlist_attrs):
        for field in attr:
            setattr(Unitlist_mock[idx], field, attr[field])

    for unit in Unitlist_mock:
        setattr(unit, 'path', os.path.join(USER_DIR, unit.id))

    return Unitlist_mock
