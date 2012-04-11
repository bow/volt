# -*- coding: utf-8 -*-
"""
---------------------------
volt.config.default_widgets
---------------------------

Volt default widgets, and jinja2 filters and tests.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

def displaytime(time, format):
    """Jinja2 filter for displaying datetime objects according to format."""
    return time.strftime(format)
