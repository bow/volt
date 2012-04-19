How Volt works
==============

The Configuration file
======================

Volt relies on a central configuration file `voltconfig.py` for much
of its customization. It consists of a general `SITE` configuration
section, which defines global site settings, and engine-specific
sections that take care of specific engine settings. (Recall, an
engine takes care of a subset of your posts and parses/handles then in
an engine-specific way, e.g. blog posts versus static pages).

:todo: Explain the differences between engines, plugins and widgets to the user.

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

**URL**
    The engine's URL specifies a relative (to the site URL) path in
    which the posts will appear.  For instance, if your ENGINE_PLAIN
    configuration has an `URL` setting `/page`, your static pages will
    appear under SITE_URL/page.

**PERMALINK**
    Each post has a canonical URL associated, under which it will be
    found.  This setting specifies the permalink pattern of articles
    for this engine. It allows the use of variables. The permalink
    pattern is appended to the SITE_URL/ENGINE_URL/ pattern.  Examples
    of possible variables are:

    * {slug}

    :todo: what else is possible?
    
**PLUGINS**

    :todo: TODO

**WIDGETS**

    :todo: TODO

**UNITS_PER_PAGINATION**

    :todo: TODO

**PAGINATIONS**
    ('','tag/{tags}', '{time:%Y/%m/%d}', '{time:%Y/%m}', '{time:%Y}'),

    :todo: TODO

**GLOBAL_FIELDS**
    If you use e.g. {tags} in your PAGINATIONS setting, all posts will
    have to have a tags attriute set, or volt will refuse to generate
    your site. You can avoid this by setting default values for
    attributes in case they are not explicitely specified. This is
    what the `GLOBAL_FIELDS` option is for.

    :todo: can this also be specified in a SITE Config, or is it
           limited to ENGINES?

    You can specify a GLOBAL_FIELDS option in the engine Config. This
    will set all Units in your blog engine that does not have a tags
    attribute to have a tags attribute with 'uncategorized' as the
    value. This way, you can set a default tag for all your blog posts
    and only have an explicit declaration for posts that you want.
    For example:

        GLOBAL_FIELDS = {'tags': ('uncategorized', )},


Engines
=======

Blog engine
-----------

Pagination
++++++++++

:todo: Explain how pagination works.

Plain engine
------------

Plugins
=======

Markup support
--------------

By default, volt assumes that file contain raw html content. Adding markup support plugins allows to support arbitrary markup. Volt supports `Markdown <http://daringfireball.net/projects/markdown/>`_, `ReSTructured Text <http://docutils.sourceforge.net/rst.html>`_, and...
:todo: describe andlist  all supported plugins.

**markdown_parser**
    Adding this plugin adds support for Markdown in .md files. The
    :mod:`markdown` package needs to be installed to support this.
    :todo: what module requirement correct?

**rst_parser**
    Adding this plugin adds support for ReSTructured Text in .rst
    files. The :mod:`docutils` package needs to be installed to
    support this.

Atom feed
---------

Adding the `atomic` plugin to the list of plugins for a specific
engine configuration will automatically create an atom feed of the
last 10 posts of this engines feed. By default only a summary of the
first 400 characters will be contained in the feed, rather than full
posts.

:todo: describe configuration options and how to get full posts.

Syntax highlighter plugin
-------------------------

Templating
==========

:todo: Describe what templates are being used, and which variables are
       available in templates. Perhaps this should go in a separate
       page of its own.
