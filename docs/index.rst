.. volt documentation master file, created by
   sphinx-quickstart on Thu Apr 19 07:57:22 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to volt's documentation!
================================

Contents:

.. toctree::
   :maxdepth: 2

Configuration
=============

Volt relies on a central configuration file `voltconfig.py` for much of its customization. It consists of a general `SITE` configuration section, which defines global site settings, and engine-specific sections that take care of specific engine settings. (Recall, an engine takes care of a subset of your posts and parses/handles then in an engine-specific way, e.g. blog posts versus static pages).

.. todo:: Explain the differences between engines, plugins and widgets to the user.

Site Configuration
------------------

**TITLE** This is simply the title of your website, the value will be
    available in you r templates as `{{ CONFIG.SITE.TITLE }}`.

    :todo: Will all settings in this section be available in the
           template in this way?

**URL** This is the URL of your website, it will, for instance, be
    used to create permalinks to single pages.

**ENGINES** This lists the engines to be used in this website. By
    default, the 'blog' and 'plain' engines are available for blog
    entries and static web pages respectively. You can easily
    customized individual engines.

**WIDGETS** Widgets add items/variables that can be used in page
    templates. The widgets listed in this section are available in all
    pages of all engines.

    :todo: Is this true?

    Widgets need to be defined in the widgets.py file in the volt root.

**FILTERS** Jinja2 filters are ...
    :todo: ?


Engine Configuration
--------------------

Engines take care of a subset of posts and publish them in specific
ways. By default, the set of posts is taken from a directory named
according to the engine, ie, the 'blog' engine handles all posts that
are in the `contents/blog' directory.

URL specifies a relative (to the site URL) path in which the posts
    will appear.  For instance, if your ENGINE_PLAIN configuration has
    an `URL` setting `/page`, your static pages will appear under
    SITE_URL/page.

PERMALINK Each post has a canonical URL associated, under which it
    will be found.  This setting specifies the permalink pattern of
    articles for this engine. It allows the use of variables. The
    permalink pattern is appended to the SITE_URL/ENGINE_URL/ pattern.
    Examples of possible variables are:

    * {slug}

    :todo: what else is possible?
    
PLUGINS

    :todo: TODO

WIDGETS

    :todo: TODO

UNITS_PER_PAGINATION

    :todo: TODO

PAGINATIONS
    ('','tag/{tags}', '{time:%Y/%m/%d}', '{time:%Y/%m}', '{time:%Y}'),
    :todo: TODO

Pagination
++++++++++

:todo: Explain how pagination works.

Templating
==========

:todo: Describe what templates are being used, and which variables are
       available in templates.

Plugins
=======

:todo: Describe what plugins can do, which ones are available.
These plugins are available in the default install:

  * **markdown_parser**
  * **atomic**
  :todo: list them all

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

