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
   <http://github.com/bow/volt/blob/master/volt/gen.py>`_ to get a picture of
   how the engines work.
  
   Finally, Volt comes with a plugin architecture that lets you hook into the
   engines' actions. Five plugins comes packed in with volt: plugins for
   atom feed generation, for syntax highlighting, and for parsing three
   different markup languages (markdown, restructured text, and textile). 
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

``pip install volt``

Volt is still in alpha and under heavy development. It's usable enough to be
used for making `a real website <http://bow.web.id>`_, but things will break
here and there.

Dependencies:

* `Jinja2 <http://jinja.pocoo.org/docs/>`_

Optional dependencies:

* `python-markdown <http://freewisdom.org/projects/python-markdown/Installation>`_
  (installed by default for ``volt demo``, can be safely removed if not used)

* `python-discount <http://github.com/trapeze/python-discount>`_, for faster
  markdown processing

* `docutils <http://docutils.sourceforge.net/>`_, for parsing restructured text
  contents

* `python-textile <https://github.com/chrisdrackett/python-textile>`_, for
  parsing textile contents

* `pygments <http://pygments.org/>`_, for syntax highlighting in pages


-----
USAGE
-----

Go through a superquick demo of Volt by running ``volt demo`` in an empty
directory and opening ``localhost:8000`` in your browser.

Here's a quick summary of the currently available commands:

* ``volt init``: Starts a Volt project, must be run inside an empty directory.
  The ``voltconf.py`` file created by this command currently contains almost all
  the default settings. You can safely edit or remove them.

* ``volt gen``: Generates the website into a ``site`` folder in your current
  project directory.

* ``volt serve``: Starts the server pointing to the ``site`` directory. Can be
  run from anywhere inside a Volt project directory.

* ``volt demo``: Starts the demo, must be run inside an empty directory.

* ``volt version``: Shows the current Volt version.

Use your own engines by writing them in an ``engines`` directory inside your
Volt project directory. Plugins follow the same rule: ``plugins`` inside your
Volt project directory.

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
