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


def activatedin(name, config):
    """Jinja2 test for checking whether an engine, plugin, or widget is active.
    
    name -- Name of engine, plugin, or widget.
    config -- UnifiedConfigContainer instance, passed as an argument at render
        time so the values are already primed.

    Example usage:
        {{ if "css_minifier" is activatedin CONFIG }}
            <p>CSS Minifier plugin is active</p>
        {{ endif }}

    or, to check whether several engines/plugins/widgets are active:
        {{ if ["css_minifier", "blog"] is activatedin CONFIG }}
            <p>CSS Minifier plugin and Blog engine are active</p>
        {{ endif }}
    """
    # no need to collect _actives if it's already set
    try:
        actives = config._actives
    # _actives not set, then compute it and do a setattr
    except AttributeError:
        engines = config.SITE.ENGINES
        plugins = config.SITE.PLUGINS
        widgets = config.SITE.WIDGETS

        for conf in config:
            try:
                plugins += getattr(conf, 'PLUGINS')
                widgets += getattr(conf, 'WIDGETS')
            # we don't care if the Config object doesn't have any plugins
            # or widgets (e.g. CONFIG.VOLT)
            except AttributeError:
                pass

        actives = set(engines + plugins + widgets)
        setattr(config, '_actives', actives)

    if isinstance(name, basestring):
        return any([name in x for x in actives])
    else:
        results = []
        for item in name:
            results.append(any([item in x for x in actives]))
        return all(results)

