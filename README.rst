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

1. **Automatic generation of paginations according to content attributes**

   Say you have a blog with 10 posts, each with its own set of tags that might
   might not be present in all posts. By only by supplying the URL pattern,
   Volt can generate the pages containing each blog post  categorized by tag,
   paginated to your liking.

   For example, you only need to supply ``tag/{tags}`` and Volt will generate
   links to ``tag/foo``, ``tag/bar``, ``tag/baz``, where each of these page
   (or ``Pack``, in Volt's internals) will contain all the posts sharing that tag.

   And this doesn't apply only to tags. You can use it to create pages based on
   authors, time (year, day, date, whatever you want), and any other data you
   put in your posts. 

   All with a simple URL pattern in the configuration file, like so ::

       PACKS = ('', 'tag/{tags}', '{time:%Y}', '{time:%Y/%m}', '{time:%Y/%m/%d}')


2. **Built-in server capable of rebuilding your entire site whenever it detects a
   change in any of the source files**

   Static sites need to be generated repeatedly to reflect changes in their source.
   After a while, doing this becomes cumbersome and annoying. Volt's server
   automatically generates your static site whenever it detects changes in the
   source, so you can focus on experimenting with your actual site contents.

3. **Modularity and extensibility**

   Under the hood, Volt is actually a collection of different engines
   responsible for different sections of your site. The blog engine, for
   example generates the blog section of your site, while the plain engine,
   generates simple web pages. `See how simple the blog engine code`_ is and 
   take a peek at the `main site generator function`_ to get a picture of how
   these engines work.
  
   Finally, Volt comes with a plugin architecture that lets you hook into the
   engines' actions. Three plugins comes packed in with volt: plugins for
   atom feed generation, for syntax highlighting, and for markdown processing. 
   `Browse their code`_ to see how you can easily write your own plugin.

4. **Centrally-managed configuration with flexible options**

   Sort your content according to time, or title, or author name, or tags,
   anything you want. Set global values for all content, e.g. authors for all
   blog posts. Define your own Jinja2 tests or filters. Set the plugin options.
   You can do all these in Volt through one central configuration file: 
   ``voltconf.py``, conveniently accessible in your project folder.

All these with the perks of static websites, of course (easy deployment,
easy back-up and tracking, security, speed, etc.)


------------
INSTALLATION
------------

``pip install volt``

Volt is still in alpha ~ it's usable enough to be used for making 
`a real website`_, but many things might still break here and there.

By default Volt will install the `python markdown module`_. You can install
`python-discount`_ to improve markdown processing speed. `python-discount`_
is a wrapper for `Discount`_, a fast markdown parser written in C.


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

See the `TODO`_ list.


----------------------
CREDITS & ATTRIBUTIONS
----------------------

Although Volt was written completely from the ground up, it is in many ways
inspired by `Blogofile`_, another Python static website generator written by 
`Ryan McGuire`_. It hasn't been updated for some time now, unfortunately, which
is one of my reasons I wrote Volt. Go check it out still if you're interested.


.. _See how simple the blog engine code: http://github.com/bow/volt/blob/master/volt/engine/blog.py
.. _main site generator function: http://github.com/bow/volt/blob/master/volt/gen.py
.. _Browse their code: http://github.com/bow/volt/tree/master/volt/plugin
.. _a real website: http://bow.web.id
.. _python markdown module: http://freewisdom.org/projects/python-markdown/Installation
.. _python-discount: http://github.com/trapeze/python-discount
.. _Discount: http://www.pell.portland.or.us/~orc/Code/discount/
.. _TODO: http://github.com/bow/volt/blob/master/TODO
.. _Blogofile: http://github.com/EnigmaCurry/blogofile
.. _Ryan McGuire: http://www.enigmacurry.com/
