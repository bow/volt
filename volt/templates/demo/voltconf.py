# -*- coding: utf-8 -*-
# Volt configurations file

import os
from volt.config import Config


# General project configurations
SITE = Config(

    # Your site name
    TITLE = 'My First Volt Site',

    # Your site URL (must be preceeded with 'http://')
    URL = 'http://localhost',

    # Engines used in generating the site
    # These represent different sections of your site
    # Available built-in engines are 'blog' and 'plain'
    # The blog engine generates blogs from text files, while the
    # plain engine generates plain web pages
    # To disable an engine, just remove its name from this list
    ENGINES = ('blog', 'plain', ),

    # Non-engine widgets
    WIDGETS = (
        'active_engines',
        #'github_search',
    ),

    # Jinja2 filters
    FILTERS = ('taglist', ),
)


# Plain engine configurations
ENGINE_PLAIN = Config(

    # URL for all page content relative to root URL
    URL = '/page',

    # Plain page permalink, relative to page URL
    PERMALINK = '{slug}',

    # Plugins to be run on plain units
    PLUGINS = (
        'markdown_parser',
    ),
)


# Blog engine configurations
ENGINE_BLOG = Config(

    # URL for all blog content relative to root URL
    URL = '/',

    # Blog posts permalink, relative to blog URL
    PERMALINK = '{time:%Y/%m/%d}/{slug}',

    # Plugins to be run on blog units
    PLUGINS = (
        'markdown_parser',
        #'atomic',
    ),

    # Widgets to be created from blog units
    WIDGETS = (
        'monthly_archive',
        #'latest_posts',
    ),

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
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'site'),
)
