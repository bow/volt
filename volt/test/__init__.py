# Mock objects for testing

import os

from mock import Mock

from volt.config import SessionConfig
from volt.config.base import Config


test_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(test_dir, 'fixtures', 'project')
blog_content_dir = os.path.join(project_dir, 'content', 'blog')

session_mock = Mock(spec=SessionConfig)
config_mocks = ['VOLT', 'SITE', 'BLOG', 'PLAIN', ]

# attach config mock objects to mock session
for mock_obj in config_mocks:
    setattr(session_mock, mock_obj, Mock(spec=Config))


# volt options
volt_opts = {
        'USER_CONF': 'voltconf.py',
        'CONTENT_DIR': os.path.join(project_dir, 'content'),
        'TEMPLATE_DIR': os.path.join(project_dir, 'templates'),
        'SITE_DIR': os.path.join(project_dir, 'site'),
        'IGNORE_PATTERN': '_*.html',
}
for key in volt_opts:
    setattr(session_mock.VOLT, key, volt_opts[key])

# site options
site_opts = {
        'TITLE': 'Mock Title',
        'DESC': 'Mock Desc',
        'ENGINES': [],
        'PLUGINS': [('', []),],
}
for key in site_opts:
    setattr(session_mock.SITE, key, site_opts[key])

# blog options
blog_opts = {
        'URL': 'blog',
        'PERMALINK': '{time:%Y/%m/%d}/{slug}',
        'CONTENT_DATETIME_FORMAT': '%Y/%m/%d %H:%M',
        'DISPLAY_DATETIME_FORMAT': '%A, %d %B %Y',
        'GLOBAL_FIELDS': {'author': ''},
        'POSTS_PER_PAGE': 10,
        'EXCERPT_LENGTH': 50,
        'CONTENT_DIR': os.path.join(volt_opts['CONTENT_DIR'], 'blog'),
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], '_post.html'),
        'PACK_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], '_pagination.html'),
        'SORT': '-time',
        'PROTECTED': ('id', 'content', ),
        'REQUIRED': ('title', 'time', ),
        'FIELDS_AS_DATETIME': ('time', ),
        'FIELDS_AS_LIST': ('tags', 'categories', ),
        'LIST_SEP': ', ',
}
for key in blog_opts:
    setattr(session_mock.BLOG, key, blog_opts[key])

# plain options
plain_opts = {
        'URL': "/",
        'PERMALINK': "{slug}",
        'CONTENT_DATETIME_FORMAT': "%Y/%m/%d %H:%M",
        'DISPLAY_DATETIME_FORMAT': "%A, %d %B %Y",
        'CONTENT_DIR': os.path.join(volt_opts['CONTENT_DIR'], "plain"),
        'UNIT_TEMPLATE_FILE': os.path.join(volt_opts['TEMPLATE_DIR'], "_plain.html"),
        'REQUIRED': ('title', ),
        'GLOBAL_FIELDS': {},
        'PROTECTED': ('id', 'content', 'parent', ),
        'FIELDS_AS_DATETIME': ('time', ),
        'FIELDS_AS_LIST': ('tags', 'categories', ),
        'LIST_SEP': ', ',
}
for key in plain_opts:
    setattr(session_mock.PLAIN, key, plain_opts[key])
