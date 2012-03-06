# Mock objects for testing

import os
from datetime import datetime

from mock import Mock

from volt.config import SessionConfig
from volt.config.base import Config
from volt.engine import Unit
from volt.test import PROJECT_DIR


# Engine mocks
Unit_Mock = Mock(spec=Unit)

Unitlist_Mock = list()
for i in range(5):
    Unitlist_Mock.append(Mock(spec=Unit))

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



# Session mock
SessionConfig_Mock = Mock(spec=SessionConfig)

configs = ['VOLT', 'SITE', 'BLOG', 'PLAIN', 'PLUGINS', 'JINJA2', ]

# attach config mock objects to mock session
for config in configs:
    setattr(SessionConfig_Mock, config, Mock(spec=Config))

# volt options
volt_opts = {
        'USER_CONF': 'voltconf.py',
        'ROOT_DIR': PROJECT_DIR,
        'CONTENT_DIR': os.path.join(PROJECT_DIR, 'content'),
        'TEMPLATE_DIR': os.path.join(PROJECT_DIR, 'templates'),
        'LAYOUT_DIR': os.path.join(PROJECT_DIR, 'layout'),
        'SITE_DIR': os.path.join(PROJECT_DIR, 'site'),
        'IGNORE_PATTERN': str(),
}
for key in volt_opts:
    setattr(SessionConfig_Mock.VOLT, key, volt_opts[key])

# site options
site_opts = {
        'TITLE': 'Mock Title',
        'URL': 'http://alay.com',
        'DESC': 'Mock Desc',
        'ENGINES': (),
        'PLUGINS': (('', []),),
        'PAGINATION_URL': '',
        'INDEX_HTML_ONLY': True,
}
for key in site_opts:
    setattr(SessionConfig_Mock.SITE, key, site_opts[key])

# blog options
blog_opts = {
        'URL': 'blog',
        'PERMALINK': '{time:%Y/%m/%d}/{slug}',
        'CONTENT_DATETIME_FORMAT': '%Y/%m/%d %H:%M',
        'DISPLAY_DATETIME_FORMAT': '%A, %d %B %Y',
        'GLOBAL_FIELDS': {'author': ''},
        'POSTS_PER_PAGE': 2,
        'EXCERPT_LENGTH': 400,
        'CONTENT_DIR': os.path.join(volt_opts['CONTENT_DIR'], 'blog'),
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], 'blog_post.html'),
        'PACK_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], 'blog_pagination.html'),
        'SORT': '-time',
        'PACKS': ('',),
        'PROTECTED': ('id', 'content', ),
        'REQUIRED': ('title', 'time', ),
        'FIELDS_AS_DATETIME': ('time', ),
        'FIELDS_AS_LIST': ('tags', 'categories', ),
        'LIST_SEP': ', ',
}
for key in blog_opts:
    setattr(SessionConfig_Mock.BLOG, key, blog_opts[key])

# plain options
plain_opts = {
        'URL': '/',
        'PERMALINK': '{slug}',
        'CONTENT_DATETIME_FORMAT': '%Y/%m/%d %H:%M',
        'DISPLAY_DATETIME_FORMAT': '%A, %d %B %Y',
        'CONTENT_DIR': os.path.join(volt_opts['CONTENT_DIR'], 'plain'),
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], 'page.html'),
        'REQUIRED': ('title', ),
        'GLOBAL_FIELDS': {},
        'PROTECTED': ('id', 'content', 'parent', ),
        'FIELDS_AS_DATETIME': ('time', ),
        'FIELDS_AS_LIST': ('tags', 'categories', ),
        'LIST_SEP': ', ',
}
for key in plain_opts:
    setattr(SessionConfig_Mock.PLAIN, key, plain_opts[key])

# jinja2 tests and filters
jinja2_opts = {
        'TESTS': dict(),
        'FILTERS': dict(),
}
