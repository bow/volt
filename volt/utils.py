# -*- coding: utf-8 -*-
"""
    volt.utils
    ~~~~~~~~~~

    General utility functions.


    :copyright: (c) 2012-2016 Wibowo Arindrarto <bow@bow.web.id>
    :license: BSD

"""


def lazyproperty(func):
    """Decorator for lazy property loading.

    This decorator adds a dictionary called ``_cached`` to the instance
    that owns the class it decorates.

    """
    attr_name = func.__name__

    @property
    def cached(self):
        if not hasattr(self, '_cached'):
            setattr(self, '_cached', {})
        try:
            return self._cached[attr_name]
        except KeyError:
            result = self._cached[attr_name] = func(self)
            return result

    return cached
