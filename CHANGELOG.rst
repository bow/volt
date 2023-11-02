.. :changelog:

Changelog
=========

This format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_ and this
project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.


Unreleased
----------
*Release date: TBD*


..


0.0.3
-----
*Release date: 24 April 2012*

Added
^^^^^

* New builtin plugins: css_minifer and js_minifier.

* New builtin jinja test: ``activatedin``, for testing whether an engine, plugin, or widget is
  active.

* New feature: widgets
  Widgets enable dynamic retrieval of Unit attributes, useful for creating things like a list
  of most recent posts or a list of archive links. They are Python functions stored in
  ``widgets.py`` in the project root directory.

* New feature: logging
  Users can now log their entire ``volt`` run and log their custom engines, plugins, or widgets.

* New command: ``volt ext``
  ``volt ext`` creates template files for writing custom engine, plugin, or widget, in the root
  project directory. It can also be used to copy builtin engines/plugins/widgets into the
  user's ``volt`` project directory.

* New settings:

  - ``SITE.LOG_LEVEL``
    Integer to set logging level, using values similar to Python's logging module.
  - ``SITE.WIDGETS``
    List of widgets that do not retrieve information from engine units.
  - ``{ENGINE}.WIDGETS``
    List of widgets that retrieve information from engine units.
  - ``{ENGINE}.PLUGINS``
    List of plugins to run on the specified engine units.
  - ``SITE.PAGES``
    List of template file names for creating pages independent from any engines. Useful for
    creating for example a main ``index.html`` file or a ``404.html`` file.
  - ``SITE.FILTERS``
    List of custom Jinja2 filters.
  - ``SITE.TESTS``
    List of custom Jinja2 tests.
  - ``SITE.SLUG_CHAR_MAP``
    Dictionary of characters to replace in a slug, useful for specifying custom non-ascii
    character replacements

Changed
^^^^^^^

* Improved console messages.

* Changed/removed these setting names/values:

  - ``{ENGINE}.CONTENT_DATETIME_FORMAT`` -> ``{ENGINE}.DATETIME_FORMAT``
  - ``VOLT.LAYOUT_DIR`` -> ``SITE.ASSET_DIR``
  - default ``VOLT.ASSET_DIR`` value is ``assets``
  - default ``VOLT.CONTENT_DIR`` value changed to ``contents`` from ``content``

* Active engines must now define a ``units`` property method that returns all its units.

* ``Engine.activate`` renamed to ``Engine.preprocess`` and is not an abstract method anymore.


Fixed
^^^^^

* ``volt serve`` now only runs ``volt gen`` once

* All ``volt`` commands work from anywhere inside a project directory now


..


0.0.2
-----
*Release date: 25 March 2012*

Added
^^^^^

* Preliminary support for more python Versions: 3.2 and 2.6

* Preliminary support for rSt and textile plugins

Changed
^^^^^^^

* Default configuration name changes:
  - ``PACKS``          -> ``PAGINATIONS``
  - ``POSTS_PER_PAGE`` -> ``UNITS_PER_PAGINATION``
  - ``SORT``           -> ``SORT_KEY``

* ``volt serve`` now generates the site first before serving any contents.

* Pygments is now an optional dependency.

* Engines and Plugins now store their default settings as a class attribute. Users can override
  this by creating a Config object with the designated name (the value of the Engine/Plugin
  class attribute ``USER_CONF_ENTRY``) in the project's ``voltconf.py``.

Removed
^^^^^^^

* PyYAML dependency.

Fixed
^^^^^

* Windows terminal output does not display ANSI color codes anymore.

* ``volt`` server regeneration now works if ``voltconf.py`` is changed.


..


0.0.1
-----
*Release date: 6 March 2012*

Added
^^^^^

* First ``volt`` release
