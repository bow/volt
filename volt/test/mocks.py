# Mock objects for testing

import os

from mock import Mock

from volt.config import SessionConfig
from volt.config.base import Config
from volt.engine import Unit
from volt.test import PROJECT_DIR


# Engine mocks
Unit_Mock = Mock(spec=Unit)


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
        'DESC': 'Mock Desc',
        'ENGINES': (),
        'PLUGINS': (('', []),),
        'PAGINATION_URL': '',
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
        'POSTS_PER_PAGE': 10,
        'CONTENT_DIR': os.path.join(volt_opts['CONTENT_DIR'], 'blog'),
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], '_post.html'),
        'PACK_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], '_pagination.html'),
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
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], '_plain.html'),
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
