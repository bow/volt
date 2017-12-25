# -*- coding: utf-8 -*-
"""
    volt.utils
    ~~~~~~~~~~

    General utility functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import sys
import importlib.util as iutil
from collections import namedtuple
from os import path
from pathlib import Path

import pytz
import pytz.exceptions as tzexc
import tzlocal


class AttrDict(dict):

    """Dictionary whose keys can be accessed as attributes."""

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(f"{self.__class__.__name__} has no attribute"
                                 f" {attr!r}")

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError as e:
            raise AttributeError(f"{self.__class__.__name__} has no attribute"
                                 f" {attr!r}")


class _Mark(object):

    """Helper class for marking results that always evaluates to False."""

    def __bool__(self):
        return False


_mark = _Mark()


# Helper tuple for containing success or failure results.
class Result(namedtuple("Result", ["data", "errs"])):

    """Container for return values that may be a success or failure.

    Instances of this class *SHOULD NOT* be created using the default
    ``__init__`` call, but rather using either the ``as_success`` or
    ``as_failure`` methods.

    """

    @classmethod
    def as_success(cls, success_value):
        """Returns a success variant with the given value."""
        return cls(success_value, _mark)

    @classmethod
    def as_failure(cls, failure_message):
        """Returns a failure variant with the given value."""
        return cls(_mark, failure_message)

    @property
    def is_failure(self):
        """Checks whether the instance represents a failure value."""
        return self.data is _mark

    @property
    def is_success(self):
        """Checks whether the instance represents a success value."""
        return self.errs is _mark


def get_tz(tzname=None):
    """Retrieves the timezone object representing the given timezone.

    If no timezone name is given, the system default will be used.

    """
    if tzname is None:
        return Result.as_success(tzlocal.get_localzone())
    try:
        return Result.as_success(pytz.timezone(tzname))
    except (AttributeError, tzexc.UnknownTimeZoneError):
        return Result.as_failure(f"cannot interpret timezone {tzname!r}")


def import_mod_attr(target):
    """Imports the attribute of a module given its string path."""
    try:
        mod_name, cls_name = target.replace(":", ".").rsplit(".", 1)
    except ValueError:
        return Result.as_failure("invalid module attribute import target:"
                                 f" {target!r}")

    if path.isfile(mod_name):
        return Result.as_failure("import from file is not yet supported")

    sys.path = [""] + sys.path if not sys.path[0] == "" else sys.path

    try:
        spec = iutil.find_spec(mod_name)
    except (ModuleNotFoundError, ValueError):
        spec = None
    if spec is None:
        return Result.as_failure(f"failed to find module {mod_name!r} for"
                                 " import")
    mod = iutil.module_from_spec(spec)
    spec.loader.exec_module(mod)

    try:
        return Result.as_success(getattr(mod, cls_name))
    except AttributeError:
        return Result.as_failure(f"module {mod_name!r} does not contain"
                                 f" attribute {cls_name!r}")


def find_pwd(fname, start=None):
    """Finds the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    """
    pwd = Path.cwd() if start is None else Path(start).expanduser().resolve()

    while pwd != pwd.parent:
        if pwd.joinpath(fname).exists():
            return Result.as_success(pwd)
        pwd = pwd.parent

    return Result.as_failure("failed to find project directory")


def calc_relpath(target: Path, ref: Path) -> Path:
    """Calculates the target's path relative to the reference.

    :param pathlib.Path target: The path to which the relative path will point.
    :param pathlib.Path ref: Reference path.
    :returns: The relative path from ``ref`` to ``to``.
    :rtype: :class:`Path`.

    """
    ref = ref.expanduser()
    target = target.expanduser()
    if not ref.is_absolute() or not target.is_absolute():
        raise ValueError("cannot compute relative paths of non-absolute"
                         " input paths")

    common = Path(path.commonpath([ref, target]))
    ref_uniq = ref.parts[len(common.parts):]
    target_uniq = target.parts[len(common.parts):]

    rel_parts = ("..",) * (len(ref_uniq)) + target_uniq

    return Path(*rel_parts)


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
