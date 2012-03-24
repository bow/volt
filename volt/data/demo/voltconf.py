# Volt configurations file

import os
from volt.config import Config


# General project configurations
SITE = Config(
    # Your site name
    TITLE = 'My First Volt Site',
    # Your site URL (must be preceeded with 'http://')
    URL = 'http://localhost',
    # Your site description
    DESC = 'Because static sites have potential',
    # Engines used in generating the site
    # These represent different sections of your site
    # Available built-in engines are 'blog' and 'plain'
    # The blog engine generates blogs from text files, while the
    # plain engine generates plain web pages
    # To disable an engine, just remove its name from this list
    ENGINES = ('blog', 'plain', ),
    # Plugins used in site generation
    # Each plugin entry is a tuple of the plugin name as string
    # and a list of its target engines
    # These are run according to the order they are listed here
    PLUGINS = (
        # volt-markdown enables posting with markdown
        ('markdown_parser', ['blog', 'plain']),
        # volt-atomic generates atom feed for the target engine
        ('atomic', ['blog']),
    ),
)

# Plain engine configurations
ENGINE_PLAIN = Config(
    # URL for all page content relative to root URL
    URL = 'page',
    # Page permalink, relative to page URL
    PERMALINK = '{slug}',
)

# Blog engine configurations
ENGINE_BLOG = Config(
    # URL for all blog content relative to root URL
    URL = '/',
    # Blog posts permalink, relative to blog URL
    PERMALINK = '{time:%Y/%m/%d}/{slug}',
    # The number of displayed posts per pagination page
    UNITS_PER_PAGINATION = 10,
    # Excerpt length (in characters) for paginated items
    EXCERPT_LENGTH = 400,
    # Paginations to build for the static site
    # Items in this tuple will be used to set the paginations relative to
    # the blog URL. Items enclosed in '{}' are pulled from the unit values,
    # e.g. 'tag/{tags}' will be expanded to 'tag/x' for x in each tags in the
    # site. These field tokens must be the last token of the pattern.
    # Use an empty string ('') to apply pagination to all blog units
    PAGINATIONS = ('','tag/{tags}', '{time:%Y/%m/%d}', '{time:%Y/%m}', '{time:%Y}'),
)

# Plugin configurations
PLUGIN_ATOMIC = Config(
    OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'site', 'atom.xml'),
)

# Jinja custom filters
def catlist(catlist):
    """Show categories in comma-separated links."""
    s = []
    for cat in catlist:
        s.append('<a href="/tag/' + cat + '/" class="button red">' + cat + '</a>')
    return ', '.join(s)

JINJA2_FILTERS = Config(
    catlist =  catlist,
)
