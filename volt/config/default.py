# -*- coding: utf-8 -*-
"""
-------------------
volt.config.default
-------------------

Volt default configurations.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

from volt.config import Config


# Changing values in this Config is allowed but not recommended
VOLT = Config(

    # User config file name
    # Used to determine project root
    USER_CONF = 'voltconf.py',

    # Directory paths for content files, templates, and generated site
    # relative to a project root
    CONTENT_DIR = 'content',
    TEMPLATE_DIR = 'templates',
    LAYOUT_DIR = 'layout',
    SITE_DIR = 'site',
)


# Default site configurations
SITE = Config(

    # Site name, URL, and description
    TITLE = 'My Volt Site',
    URL = str(),
    DESC = str(),

    # Engines used in generating the site
    # Defaults to none
    ENGINES = tuple(),

    # Plugins used in site generation
    # Tuple of tuples, each containing a string for the plugin file name
    # and list of engine names indicating which engine to target
    # Run according to order listed here
    # Defaults to none
    PLUGINS = (('',[]),),

    # URL to use for pagination
    # This will be used for paginated items after the first one
    # For example, if the pagination URL is 'page', then the second
    # pagination page will have '.../page/2/', the third '.../page/3/', etc.
    PAGINATION_URL = '',

    # Boolean to set if output file names should all be 'index.html' or vary
    # according to the last token in its self.permalist attribute
    # index.html-only outputs allows for nice URLS without fiddling too much
    # with .htaccess
    INDEX_HTML_ONLY = True,

    # Ignore patterns
    # Filenames that match this pattern will not be copied from template directory
    # to site directory
    IGNORE_PATTERN = str(),
)


# Built-in Jinja2 filters
def displaytime(time, format):
    """Show time according to format."""
    return time.strftime(format)

JINJA2_FILTERS = Config(
    displaytime = displaytime,
)


# Built-in Jinja2 tests
JINJA2_TESTS = Config()
