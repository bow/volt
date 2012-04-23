# -*- coding: utf-8 -*-
"""
---------------------------
volt.config.default_widgets
---------------------------

Volt default widgets, and jinja2 filters and tests.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""

def displaytime(datetime_obj, format):
    """Jinja2 filter for displaying datetime objects according to format.

    datetime_obj -- Datetime object.
    format -- String of datetime format.

    Example usage:
        {{ page.time|displaytime("%Y") }} will output, for example "2012".
    """
    return datetime_obj.strftime(format)


def activein(name, config):
    """Jinja2 test for checking whether an engine, plugin, or widget is active.
    
    name -- Name of engine, plugin, or widget.
    config -- UnifiedConfigContainer instance, passed as an argument at render
        time so the values are already primed.

    Example usage:
        {{ if "css_minifier" is activein CONFIG }}
            <p>CSS Minifier plugin is active</p>
        {{ endif }}
    """
    engines = config.SITE.ENGINES
    plugins = config.SITE.PLUGINS
    widgets = config.SITE.WIDGETS

    for conf in config:
        if hasattr(conf, 'PLUGINS'):
            plugins += getattr(conf, 'PLUGINS')
        if hasattr(conf, 'WIDGETS'):
            widgets += getattr(conf, 'WIDGETS')

    return any([name in x for x in (engines, plugins, widgets)])
