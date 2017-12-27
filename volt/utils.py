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
from typing import Any, Generic, Optional, TypeVar

import pytz
import pytz.exceptions as tzexc
import tzlocal
from pytz.tzinfo import DstTzInfo


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


class Mark(object):

    """Helper class for marking a :class:`Result` attribute that should be
    ignored.

    Instances of this class always evaluates to ``False``.

    """

    def __bool__(self):
        return False


# The singleton used by Result.
_mark = Mark()
# Type parameter for Result.
T = TypeVar("T")


# Helper tuple for containing success or failure results.
class Result(namedtuple("Result", ["data", "errs"]), Generic[T]):

    """Container for return values that may be a success or failure.

    Instances of this class *SHOULD NOT* be created using the default
    ``__init__`` call, but rather using either the ``as_success`` or
    ``as_failure`` methods.

    """

    @classmethod
    def as_success(cls, success_value: T) -> "Result[T]":
        """Returns a success variant with the given value."""
        return cls(success_value, _mark)

    @classmethod
    def as_failure(cls, failure_message: str) -> "Result[Mark]":
        """Returns a failure variant with the given value."""
        return cls(_mark, failure_message)

    @property
    def is_failure(self) -> bool:
        """Checks whether the instance represents a failure value."""
        return self.data is _mark

    @property
    def is_success(self) -> bool:
        """Checks whether the instance represents a success value."""
        return self.errs is _mark


def get_tz(tzname: Optional[str]=None) -> Result[DstTzInfo]:
    """Retrieves the timezone object with the given name.

    If no timezone name is given, the system default will be used.

    :param tzname: Name of the timezone to retrieve.
    :type tzname: str or None
    :returns: The timezone object or a message indicating failure.
    :rtype: :class:`Result`

    """
    if tzname is None:
        return Result.as_success(tzlocal.get_localzone())
    try:
        return Result.as_success(pytz.timezone(tzname))
    except (AttributeError, tzexc.UnknownTimeZoneError):
        return Result.as_failure(f"cannot interpret timezone {tzname!r}")


def import_mod_attr(target: str) -> Result[Any]:
    """Imports the attribute of a module given its string path.

    For example, specifying ``pathlib.Path`` is essentially the same as
    executing ``from pathlib import Path```.

    :param str target: The target object to import.
    :returns: The object indicated by the input or an error message indicating
        failure.
    :rtype: :class:`Result`

    """
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


def find_pwd(fname: str, start: Optional[Path]=None) -> Result[Path]:
    """Finds the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param str fname: The filename that should be present in the directory.
    :param start: The path from which lookup should start. If given as
        ``None``, lookup will start from the current directory.
    :returns: The path to the directory that contains the filename or an error
        message indicating failure.
    :rtype: :class:`Result`

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
    :rtype: :class:`Path`

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

    :param callable func: The instance method to decorate.

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
