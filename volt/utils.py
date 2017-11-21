# -*- coding: utf-8 -*-
"""
    volt.utils
    ~~~~~~~~~~

    General utility functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from collections import namedtuple, Mapping


# Helper tuple for containing success or failure results.
class Result(namedtuple("Result", ["result", "errors"])):

    @classmethod
    def as_success(cls, success_value):
        """Returns the success value, with the error value set to an empty
        list."""
        return cls(success_value, [])

    @classmethod
    def as_failure(cls, failure_message):
        """Returns the error value in a list, with the success value set to
        None."""
        msg = [failure_message] if isinstance(failure_message, str) else \
            failure_message
        return cls(None, msg)


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


def nested_update(one, other):
    """Update function that respects nested values.

    This is similar to Python's dict.update, except when the value to
    be updated is an instance of :class:`collections.Mapping`, the
    function will recurse.

    """
    for key, value in other.items():
        if isinstance(value, Mapping):
            nv = nested_update(one.get(key, {}), value)
            one[key] = nv
        else:
            one[key] = other[key]

    return one
