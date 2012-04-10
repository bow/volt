---
title: Hello, World!
tags: static, sites, yeah
time: 2012/03/06 14:01
---

Welcome to your first Volt website!

Volt is a static website generator that strives for versatility and
ease of use. It is written in pure Python, backed by the powerful Jinja2
template engine. Use it to generate static HTML files once and serve the
resulting website anywhere you want.

This website is a small example of what you can do with Volt. Everything
needed to generate this site was taken from three source directories:
**contents**, containing the actual contents of the site;
**templates**, containing the HTML template files, and
**assets**, for all other files such as css or image files. All
settings that determines the behaviors and looks of the generated site are
configurable via **voltconf.py**, Volt's central configuration file.

Play around with the source files and see how it affects this site by
running **volt gen** and **volt serve** afterwards. Finally,
start building your own Volt site by running **volt init** and have
fun :)!
