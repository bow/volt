====
VOLT
====

-----------------------------------------------------------
Python static website generator -- with batteries included!
-----------------------------------------------------------

Volt is a static website generator written in Python. It generates entire
websites using simple plain text files with easy-to-configure options.

Templates using the Jinja2 template engine.
Posts can be written in simple plaintext, or several markup language. Volt comes packed with a Plugin for Markdown.



You should use static sites if you want sites that are:
- simple, everything is configured via text files
- secure, in the live site, it's only the server and volt's html files. No extra executables, no databases means less attack points.
- fast, all web pages are pre made so the server only needs to serve the files without performing complex operations on the fly
- easy to deploy, since it's just HTML, CSS, and possibly JS, all modern web servers can be used host static sites. Additionally, you can ftp/ssh/git-push content to update the website.
- easy to back-up and track. all contents are trackable using popular version control systems, e.g. git or hg.

You shouldn't use it if:
- your site needs to perform complex calculations
- you want your site to be able to accept user-submitted data (workaround for comments is disqus, but in other cases it's not possible). e.g. can't have contact forms
- 


Why use volt when there are many other static website generators out there?
- it's highly configurable. use different filters and engines, apply your own custom jinja2 tests or filters, color your terminal outputs, generate any permalink pattern you want, change directory names, template names, (or not). All these configurable from a single file.
- it's extensible, easy to write your own engines and plugins.
- it's easy to manage; clean separation of content, layouts, and templates
- it comes with convenient extras, bash script for command completion, basic and demo project examples, a built-in webserver able to detect file changes
- it's written in python!


Tips and tricks
- deployment using ssh/git/rsync/fabfile
- 


----------------------
CREDITS & ATTRIBUTIONS
----------------------

Although Volt was written completely from the ground up, it is in many ways
inspired by `Blogofile`_, another Python static website generator written by 
`Ryan McGuire`_. Go check it out as well.


.. _Blogofile: https://github.com/EnigmaCurry/blogofile
.. _Ryan McGuire: http://www.enigmacurry.com/
