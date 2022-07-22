"""General utility functions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import importlib.util as iutil
from os import path, PathLike
from pathlib import Path
from types import ModuleType
from typing import IO, Any, Optional

import jinja2.exceptions as j2exc
from click import echo, style
from click._compat import get_text_stderr
from jinja2 import Environment, Template
from pendulum.tz import local_timezone
from pendulum.tz.timezone import Timezone
from pendulum.tz.zoneinfo.exceptions import InvalidTimezone
from thefuzz import process

from . import exceptions as excs


def echo_fmt(msg: str, style: str = "", file: Optional[IO[Any]] = None) -> None:
    """Show a formatted message"""
    if file is None:
        file = get_text_stderr()
    echo(f"{style} {msg}", file=file)


def echo_info(msg: str, file: Optional[IO[Any]] = None) -> None:
    """Show a formatted info message."""
    echo_fmt(msg, style(" INF ", bg="blue", bold=True), file)


def echo_err(msg: str, file: Optional[IO[Any]] = None) -> None:
    """Show a formatted error message."""
    echo_fmt(msg, style(" ERR ", bg="red", bold=True), file)


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
        raise excs.VoltTimezoneError(tzname) from e


def import_file(fp: str | bytes | PathLike, mod_name: str) -> ModuleType:
    """Import the given file as the given module name"""

    spec = iutil.spec_from_file_location(mod_name, fp)
    if spec is None:
        raise excs.VoltResourceError("not an importable file: {fp}")

    mod = iutil.module_from_spec(spec)

    spec.loader.exec_module(mod)  # type: ignore

    return mod


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
        raise ValueError("could not compute relative paths of non-absolute input paths")

    common = Path(path.commonpath([ref, target]))
    common_len = len(common.parts)
    ref_uniq = ref.parts[common_len:]
    target_uniq = target.parts[common_len:]

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
        raise excs.VoltResourceError(f"could not find template {name!r}") from e
    except j2exc.TemplateSyntaxError as e:
        raise excs.VoltResourceError(
            f"template {name!r} has syntax errors: {e.message}"
        ) from e

    return template


def get_fuzzy_match(
    query: str,
    ext: str,
    cutoff: int = 50,
    *dirs: Path,
) -> Optional[str]:
    """Return a fuzzy-matched path to a file in one of the given directories"""

    fp_map = {}
    for d in dirs:
        fp_map.update({p: f"{p.relative_to(d)}" for p in d.rglob(f"*{ext}")})

    _, _, match_fp = process.extractOne(query, fp_map, score_cutoff=cutoff) or (
        None,
        None,
        None,
    )

    return match_fp


def infer_front_matter(query: str, title: Optional[str]) -> str:
    fm = {}
    default_title = Path(query).stem

    title = " ".join([tok.capitalize() for tok in (title or default_title).split("-")])
    fm["title"] = title

    *section, _ = query.rsplit("/", 1)
    ns = len(section)
    if ns == 1:
        fm["section"] = section[0]
    elif ns > 1:
        raise ValueError(f"unexpected query pattern: {query!r}")

    strv = "\n".join([f"{k}: {v}" for k, v in fm.items()])

    return f"""---\n{strv}\n---"""
