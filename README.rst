====
VOLT
====

--------------------------------------------------
The Python static website generator with potential
--------------------------------------------------

**Another static website generator?**

Sure, why not :)? The number of static site generators is continuously
growing, but so far I have yet to find a flexible static site that suits my
needs. So I decided to write my own.

**What's so different about Volt?**

Here are some of my favorite features:

1. **Automatic pagination**

   Say you have a blog with 10 posts, each with its own set of tags that might
   might not be present in all posts. By only by supplying the URL pattern,
   Volt can generate the pages containing each blog post  categorized by tag,
   paginated to your liking.

   For example, you only need to supply ``tag/{tags}`` and Volt will generate
   links to the pages ``tag/foo``, ``tag/bar``, ``tag/baz``, where each of these
   page will contain all the posts sharing that tag.

   And this doesn't apply only to tags. You can use it to create pages based on
   authors, time (year, day, date, whatever you want), and any other data you
   put in your posts. 

   All with a simple URL pattern in the configuration file, like so ::

       PAGINATIONS = ('', 'tag/{tags}', '{time:%Y}', '{time:%Y/%m}', '{time:%Y/%m/%d}')


2. **Auto-regenerating built-in server**

   Static sites need to be generated repeatedly to reflect changes in their source.
   After a while, doing this becomes cumbersome and annoying. Volt's server
   automatically generates your static site whenever it detects changes in the
   source and the configuration file, so you can focus on experimenting with your
   actual site contents.


3. **Modularity and extensibility**

   Under the hood, Volt is actually a collection of different engines
   responsible for different sections of your site. The blog engine, for
   example generates the blog section of your site, while the plain engine,
   generates simple web pages. `See how simple the blog engine code is
   <http://github.com/bow/volt/blob/master/volt/engine/builtins/blog.py>`_ 
   or take a peek at the `main site generator function 
   <http://github.com/bow/volt/blob/master/volt/generator.py>`_ to get a
   picture of how the engines work.
  
   Finally, Volt comes with a plugin architecture that lets you hook into the
   engines' actions. Seven plugins comes packed in with volt: 

   - Atom feed generator plugin (atomic, no extra dependency)

   - Markup processing plugins:

     - reStructured text (rst_parser, requires
       `docutils <http://docutils.sourceforge.net/>`_)

     - Markdown (markdown_parser, requires `python-markdown
       <http://freewisdom.org/projects/python-markdown/Installation>`_ or
       `python-discount <http://github.com/trapeze/python-discount>`_)

     - Textile (textile_parser, requires `python-textile 
       <https://github.com/chrisdrackett/python-textile>`_)
   
   - Syntax highlighter plugin (syntax, requires `pygments
     <http://pygments.org/>`_)

   - CSS minifier plugin (css_minifier, requires `cssmin
     <https://github.com/zacharyvoase/cssmin>`_)

   - Javascript minifier plugin (js_minifier, requires `jsmin
     <http://pypi.python.org/pypi/jsmin>`_)

   `Browse their code 
   <http://github.com/bow/volt/tree/master/volt/plugin/builtins>`_ 
   to see how you can easily write your own plugin.


4. **Centrally-managed configuration with flexible options**

   Sort your content according to time, or title, or author name, or tags,
   anything you want. Set global values for all content, e.g. authors for all
   blog posts. Define your own Jinja2 tests or filters. Set the plugin options.
   You can do all these in Volt through one central configuration file: 
   ``voltconf.py``, conveniently accessible in your project folder.


All these with the perks of static websites: easy deployment,
easy back-up and tracking, security, and speed.


------------
INSTALLATION
------------

Latest version from PyPI (0.0.2): ``pip install volt``

Bleeding edge from main development repo: ``pip install git+https://github.com/bow/volt.git``

Volt is still in alpha and under heavy development. Things will break here and
there, but it's usable enough for creating real websites:

* `bow.web.id <http://bow.web.id/>`_ (`source <http://github.com/bow/volt>`_,
  using the latest development version)

* `spaetzblog <http://sspaeth.de/>`_

Dependency:

* `Jinja2 <http://jinja.pocoo.org/docs/>`_

Optional dependencies:

* `python-markdown <http://freewisdom.org/projects/python-markdown/Installation>`_
  (installed by default for ``volt demo``, can be safely removed if not used)


-----
USAGE
-----

Go through a superquick demo of Volt by running ``volt demo`` in an empty
directory and opening ``localhost:8000`` in your browser.

Here's a quick summary of the currently available commands:

* ``volt init``: Starts a Volt project, must be run inside an empty directory.
  The ``voltconf.py`` file created by this command currently contains almost all
  the default settings. You can safely edit or remove them.

* ``volt demo``: Starts the demo, must be run inside an empty directory.

* ``volt gen``: Generates the website into a ``site`` folder in your current
  project directory.

* ``volt serve``: Generates the website and Starts the server pointing to the
  ``site`` directory.

* ``volt ext``: Adds a template for writing your custom engine, plugin, or
  widget. Custom engines and plugins are stored respectively inside the 
  ``engines`` and ``plugins`` directory in the root Volt project directory.
  Widgets are stored inside ``widgets.py`` in the same directory. You can also
  specify an additional ``--builtin`` to copy a builtin engine/plugin/widget
  to your Volt project directory.

* ``volt version``: Shows the current Volt version.

All of the commands except for ``init`` and ``demo`` can be run from anywhere
inside a Volt project directory.

The docs are, unfortunately, minimum at the moment. For now, the source is the
primary documentation.


-----
PLANS
-----

See the `TODO <https://github.com/bow/volt/blob/master/TODO>`_ list.


-----------
ATTRIBUTION
-----------

Volt was inspired by `Blogofile <http://github.com/EnigmaCurry/blogofile>`_,
which unfortunately has `ceased development 
<https://groups.google.com/d/msg/blogofile-discuss/MG02xNwS8Lc/_MK-gmOU2iEJ>`_.
