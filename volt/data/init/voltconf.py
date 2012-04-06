# Volt configurations file

from volt.config import Config


# Default site configurations
SITE = Config(

    # Site name
    TITLE = 'My Volt Site',

    # Site URL, used for generating absolute URLs
    URL = 'http://mysite.com',

    # Engines used in generating the site
    # Defaults to none, available choices are 'blog' and 'plain'
    ENGINES = (),

    # Plugins used in site generation
    # Tuple of tuples, each containing a string for the plugin file name
    # and list of engine names indicating which engine to target
    # Run according to order listed here
    # Defaults to none
    PLUGINS = (('',[]),),

    # Extra pages to write that are not controlled by an engine
    # Examples: 404.html, index.html (if not already written by an engine)
    # The tuple should list template names of these pages, which should
    # be present in the default template directory
    EXTRA_PAGES = (),

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
    # Filenames that match this pattern will not be copied from layout directory
    # to site directory
    IGNORE_PATTERN = '',
)


# Built-in Jinja2 filters
JINJA2_FILTERS = Config()


# Built-in Jinja2 tests
JINJA2_TESTS = Config()
