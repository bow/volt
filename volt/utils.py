# -*- coding: utf-8 -*-
"""
    volt.utils
    ~~~~~~~~~~

    General utility functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>

import importlib.util as iutil
import sys
from os import path
from pathlib import Path
from typing import Any, Callable, Optional

import jinja2.exceptions as j2exc
from jinja2 import Environment, Template
from pendulum.tz import local_timezone
from pendulum.tz.timezone import Timezone
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone

from . import exceptions as exc


def get_tz(tzname: Optional[str] = None) -> Timezone:
    """Retrieve the timezone object with the given name.

    If no timezone name is given, the system default will be used.

    :param tzname: Name of the timezone to retrieve.

    :returns: The timezone object.

    :raises ~volt.exceptions.VoltTimezoneError: when the given timezone string
        could not be converted to a timezone object.

    """
    if tzname is None:
        return local_timezone()
    try:
        return Timezone(tzname)
    except (AttributeError, ValueError, InvalidTimezone) as e:
        raise exc.VoltTimezoneError(tzname) from e


def import_mod_attr(target: str) -> Any:
    """Import the attribute of a module given its string path.

    For example, specifying ``pathlib.Path`` will execute
    ``from pathlib import Path``` statement.

    :param target: The target object to import.

    :returns: The object indicated by the input.

    :raises ~volt.exceptions.VoltResourceError: when the target could not be
        imported

    """
    try:
        mod_name, cls_name = target.replace(":", ".").rsplit(".", 1)
    except ValueError as e:
        raise exc.VoltResourceError(
            f"invalid module attribute import target: {target!r}"
        ) from e

    if path.isfile(mod_name):
        raise exc.VoltResourceError("import from file is not yet supported")

    sys.path = [""] + sys.path if not sys.path[0] == "" else sys.path

    try:
        spec = iutil.find_spec(mod_name)
        # Spec can be None if mod_name could not be found, so we raise the
        # exception manually.
        if spec is None:
            raise ModuleNotFoundError(f"No module named {mod_name}")
    except (ModuleNotFoundError, ValueError) as e:
        raise exc.VoltResourceError(f"failed to import {mod_name!r}") from e

    mod = iutil.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    try:
        return getattr(mod, cls_name)
    except AttributeError:
        raise exc.VoltResourceError(
            f"module {mod_name!r} does not contain attribute {cls_name!r}"
        )


def find_dir_containing(
    fname: str,
    start: Optional[Path] = None,
) -> Optional[Path]:
    """Find the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param fname: The filename that should be present in the directory.
    :param start: The path from which lookup starts. If set to ``None``, lookup
        starts from the current directory.

    :returns: The path to the directory that contains the filename or None if
        no such path can be found.

    """
    pwd = Path.cwd() if start is None else Path(start).expanduser().resolve()

    while pwd != pwd.parent:
        if pwd.joinpath(fname).exists():
            return pwd
        pwd = pwd.parent

    return None


def calc_relpath(target: Path, ref: Path) -> Path:
    """Calculate the target's path relative to the reference.

    :param target: The path to which the relative path will point.
    :param ref: Reference path.

    :returns: The relative path from ``ref`` to ``to``.

    :raises ValueError: when one of the given input paths is not an absolute
        path.

    """
    ref = ref.expanduser()
    target = target.expanduser()
    if not ref.is_absolute() or not target.is_absolute():
        raise ValueError(
            "could not compute relative paths of non-absolute input paths"
        )

    common = Path(path.commonpath([ref, target]))
    ref_uniq = ref.parts[len(common.parts):]
    target_uniq = target.parts[len(common.parts):]

    rel_parts = ("..",) * (len(ref_uniq)) + target_uniq

    return Path(*rel_parts)


def load_template(env: Environment, name: str) -> Template:
    """Load a template from the given environment.

    :param env: Jinja2 template environment.
    :param name: Template name to load.

    :returns: A Jinja2 template.

    :raises `~volt.exceptions.VoltResourceError`: when the template does not
        exist or it could not be instantiated.

    """
    try:
        template = env.get_template(name)
    except j2exc.TemplateNotFound as e:
        raise exc.VoltResourceError(f"could not find template {name!r}") from e
    except j2exc.TemplateSyntaxError as e:
        raise exc.VoltResourceError(
            f"template {name!r} has syntax errors: {e.message}"
        ) from e

    return template


def lazyproperty(func: Callable) -> Callable:
    """Decorator for lazy property loading.

    This decorator adds a dictionary called ``_cached`` to the instance
    that owns the class it decorates.

    :param callable func: The instance method to decorate.

    """
    attr_name = func.__name__

    @property  # type: ignore
    def cached(self):  # type: ignore
        if not hasattr(self, '_cached'):
            setattr(self, '_cached', {})
        try:
            return self._cached[attr_name]
        except KeyError:
            result = self._cached[attr_name] = func(self)
            return result

    return cached
