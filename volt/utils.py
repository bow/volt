"""General utility functions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import subprocess as sp
import importlib.util as iutil
from locale import getlocale
from os import path, scandir, PathLike
from pathlib import Path
from shutil import which
from types import ModuleType
from typing import IO, Any, Optional

from click import echo, style
from click._compat import get_text_stderr
from thefuzz import process

from . import exceptions as excs


def echo_fmt(
    msg: str,
    style: str = "",
    file: Optional[IO[Any]] = None,
    capitalize: bool = True,
) -> None:
    """Show a formatted message"""
    if file is None:
        file = get_text_stderr()
    msg = msg[0].upper() + msg[1:] if capitalize else msg
    echo(f"{style} {msg}", file=file)


def echo_info(msg: str, **kwargs: Any) -> None:
    """Show a formatted info message."""
    echo_fmt(msg, style(" INF ", bg="blue", bold=True), **kwargs)


def echo_err(msg: str, **kwargs: Any) -> None:
    """Show a formatted error message."""
    echo_fmt(msg, style(" ERR ", bg="red", bold=True), **kwargs)


def import_file(fp: str | bytes | PathLike, mod_name: str) -> ModuleType:
    """Import the given file as the given module name"""

    spec = iutil.spec_from_file_location(mod_name, fp)
    if spec is None:
        raise excs.VoltResourceError(f"not an importable file: {str(fp)}")

    mod = iutil.module_from_spec(spec)

    spec.loader.exec_module(mod)  # type: ignore

    return mod


def find_dir_containing(fname: str, start: Path) -> Optional[Path]:
    """Find the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param fname: The filename that should be present in the directory.
    :param start: The path from which lookup starts.

    :returns: The path to the directory that contains the filename or None if
        no such path can be found.

    """
    pwd = Path(start).expanduser().resolve()

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


def get_fuzzy_match(
    query: str,
    ext: str,
    start_dir: Path,
    ignore_dirname: Optional[str] = None,
    cutoff: int = 50,
) -> Optional[str]:
    """Return a fuzzy-matched path to a file in one of the given directories"""

    dirs = walk_dirs(start_dir=start_dir, ignore_dirname=ignore_dirname)

    fp_map = {}
    for d in dirs:
        fp_map.update({p: f"{p.relative_to(d)}" for p in d.glob(f"*{ext}")})

    _, _, match_fp = process.extractOne(query, fp_map, score_cutoff=cutoff) or (
        None,
        None,
        None,
    )

    return match_fp


def walk_dirs(start_dir: Path, ignore_dirname: Optional[str] = None) -> list[Path]:
    """Return the input directory and all its children directories"""

    todo_dirs = [start_dir]
    dirs: list[Path] = []

    while todo_dirs:
        cur_dir = todo_dirs.pop()
        dirs.append(cur_dir)
        for entry in scandir(cur_dir):
            if not entry.is_dir():
                continue
            p = Path(entry.path)
            if ignore_dirname is not None and p.name == ignore_dirname:
                continue
            todo_dirs.append(p)

    return dirs


def infer_lang() -> Optional[str]:
    lang_code, _ = getlocale()
    if lang_code is None:
        return None
    try:
        lang, _ = lang_code.split("_", 1)
    except ValueError:
        return None
    return lang


def infer_author(stdout_encoding: str = "utf-8") -> Optional[str]:
    git_exe = "git"
    if which(git_exe) is None:
        return None

    proc = sp.run([git_exe, "config", "--get", "user.name"], capture_output=True)
    if proc.returncode != 0:
        return None

    author = proc.stdout.strip().decode(stdout_encoding) or None

    return author


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
