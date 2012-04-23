# -*- coding: utf-8 -*-
# Volt configurations

from volt.config import Config


# Default site configurations
SITE = Config(

    # Site name
    TITLE = 'My Volt Site',

    # Site URL, used for generating absolute URLs
    URL = 'http://mysite.com',

    # Engines used in generating the site
    # Defaults to none
    ENGINES = (),

    # Extra pages to write that are not controlled by an engine
    # Examples: 404.html, index.html (if not already written by an engine)
    # The tuple should list template names of these pages, which should
    # be present in the default template directory
    PAGES = (),

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

    # Logging level
    # If set to 10, Volt will write logs to a file
    # 30 is logging.WARNING
    LOG_LEVEL = 30,

    # Ignore patterns
    # Filenames that match this pattern will not be copied from asset directory
    # to site directory
    IGNORE_PATTERN = '',

    # String replacement scheme for slugs
    # Dictionary, key is the string to replace, value is the replacement string
    # This is used to replace non-ascii consonants or vowels in a slug with
    # their ascii equivalents, so the slug meaning is preserved.
    # For example {u'ß': 'ss'}, would transfrom the slug "viel-Spaß" to
    # "viel-spass" instead of "viel-spa", preserving its meaning
    SLUG_CHAR_MAP = {},

    # Site plugins
    # These are plugins that work on the whole site
    PLUGINS = (),

    # Site widgets
    # These are widgets that work on the whole site
    WIDGETS = (),

    # Jinja2 filter function names
    FILTERS = (),

    # Jinja2 test function names
    TESTS = (),
)
