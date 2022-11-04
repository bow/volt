"""Functions invoked in a single execution session."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import bdb
import os
import subprocess as sp
import time
from contextlib import suppress
from locale import getlocale
from pathlib import Path
from shutil import which
from typing import Optional

import click
import pendulum
import structlog
from structlog.contextvars import (
    bind_contextvars,
    bound_contextvars,
    unbind_contextvars,
)
from thefuzz import process

from . import constants, error as err
from .config import Config, _VCS
from .server import _Rebuilder, make_server
from .site import Site


__all__ = ["build", "edit", "new", "serve"]


log = structlog.get_logger(__name__)


def new(
    dirname: Optional[str],
    invoc_dir: Path,
    project_dir: Path,
    name: str,
    url: str,
    author: Optional[str],
    description: str,
    language: Optional[str],
    force: bool,
    vcs: Optional[_VCS],
    config_fname: str = constants.CONFIG_FNAME,
) -> Path:
    """Create a new project.

    This function may overwrite any preexisting files and or directories
    in the target working directory.

    :param dirname: Name of the directory in which the project is created.
    :param invoc_dir: Path to the invocation directory.
    :param project_dir: Path to the parent directory in which ``dirname`` is created.
    :param name: Name of the static site, to be put inside the generated config file.
    :param url: URL of the static site, to be put inside the generated config file.
    :param description: Description of the site, to be put inside the generated
        config file.
    :param description: Language of the site, to be put inside the generated
        config file. If set to ``None``, the value will be inferred from the system
        locale.
    :param force: Whether to force project creation in nonempty directories or not.
    :param vcs: Version control system to initialize in the newly created project.
    :param config_name: Name of the config file to generate.

    :raises ~volt.error.VoltCliError:
        * when the given project directory is not empty and force is False.
        * when any directory creation fails.

    """
    project_dir = _bootstrap_project_dirs(invoc_dir, project_dir, dirname, force)

    if not name and dirname is not None:
        name = project_dir.name

    # Create initial YAML config file.
    new_conf = f"""---
# Volt configuration file.
name: "{name}"
url: "{url}"
description: "{description}"
author: "{author or (_infer_author() or '')}"
language: "{language or (_infer_lang() or '')}"
"""

    # Create initial YAML config file.
    (project_dir / config_fname).write_text(new_conf)

    if vcs is None:
        log.debug("skipping vcs initialization as no vcs is requested")
        return project_dir

    with bound_contextvars(vcs=vcs, project_dir=project_dir):

        log.debug("initializing vcs")
        match vcs:
            case "git":
                initialized = _initialize_git(project_dir)
                if not initialized:
                    log.debug("failed to initialize vcs")
            case _:
                raise ValueError(f"unknown vcs: {vcs!r}")

    return project_dir


def build(
    config: Config,
    clean: bool = True,
    with_drafts: bool = False,
) -> Optional[Site]:
    """Build the site.

    This function may overwrite and/or remove any preexisting files
    and or directories.

    :param config: Site configuration.
    :param clean: Whether to remove the entire site output directory prior
        to building, or not.

    """
    config._with_drafts = with_drafts
    log_attrs = {"drafts": with_drafts}
    bind_contextvars(**log_attrs)

    start_time = time.monotonic()
    config["build_time"] = pendulum.now()

    site: Optional[Site] = None

    try:
        site = Site(config)
        site.build(clean=clean)
        log.info("build completed", duration=f"{(time.monotonic() - start_time):.2f}s")
    except bdb.BdbQuit:
        unbind_contextvars(*log_attrs.keys())
        log.warn("exiting from debugger -- build may be compromised")
    except Exception:
        msg = "build failed"
        build_exists = False
        target_dir = config.target_dir
        with suppress(Exception):
            if target_dir.exists() and any(True for _ in target_dir.iterdir()):
                build_exists = True
        if build_exists:
            msg += " -- keeping current build"
        log.error(msg)
        raise

    return site


def edit(
    config: Config,
    query: str,
    create: Optional[str] = None,
    title: Optional[str] = None,
    lookup_drafts: bool = False,
) -> None:
    """Open a draft file in an editor."""

    if create is not None:
        fn = Path(config.drafts_dirname) / create / query
        new_fp = fn.with_suffix(constants.MARKDOWN_EXT)
        new_fp.parent.mkdir(parents=True, exist_ok=True)
        if new_fp.exists():
            click.edit(filename=f"{new_fp}")
            return None

        contents = click.edit(
            text=_infer_front_matter(query, title),
            extension=constants.MARKDOWN_EXT,
            require_save=False,
        )
        if contents:
            log.info(
                f"created new draft at {str(new_fp.relative_to(config.invoc_dir))!r}"
            )
            new_fp.write_text(contents)

        return None

    match_fp = _get_fuzzy_match(
        query=query,
        ext=constants.MARKDOWN_EXT,
        start_dir=config.sources_dir,
        ignore_dirname=None if lookup_drafts else config.drafts_dirname,
    )
    if match_fp is not None:
        click.edit(filename=f"{match_fp}")
        return None

    raise err.VoltResourceError(f"found no matching file for {query!r}")


def serve(
    config: Config,
    host: Optional[str],
    port: int,
    rebuild: bool,
    pre_build: bool,
    build_with_drafts: bool,
    build_clean: bool,
) -> None:

    eff_host = "127.0.0.1"
    if host is not None:
        eff_host = host
    elif config.in_docker:
        eff_host = "0.0.0.0"

    serve = make_server(config, eff_host, port)

    if not rebuild:
        serve()

    else:

        def builder() -> None:
            nonlocal config
            try:
                # TODO: Only reload config post-init, on config file change.
                config = config.reload()
                build(config, build_clean, build_with_drafts)
            except Exception as e:
                log.exception(e)

        with _Rebuilder(config, builder):
            if pre_build:
                builder()
            log.debug("starting dev server")
            serve()


def _get_fuzzy_match(
    query: str,
    ext: str,
    start_dir: Path,
    ignore_dirname: Optional[str] = None,
    cutoff: int = 50,
) -> Optional[str]:
    """Return a fuzzy-matched path to a file in one of the given directories"""

    dirs = _walk_dirs(start_dir=start_dir, ignore_dirname=ignore_dirname)

    fp_map = {}
    for d in dirs:
        fp_map.update({p: f"{p.relative_to(d)}" for p in d.glob(f"*{ext}")})

    _, _, match_fp = process.extractOne(query, fp_map, score_cutoff=cutoff) or (
        None,
        None,
        None,
    )

    return match_fp


def _walk_dirs(start_dir: Path, ignore_dirname: Optional[str] = None) -> list[Path]:
    """Return the input directory and all its children directories"""

    todo_dirs = [start_dir]
    dirs: list[Path] = []

    while todo_dirs:
        cur_dir = todo_dirs.pop()
        dirs.append(cur_dir)
        for entry in os.scandir(cur_dir):
            if not entry.is_dir():
                continue
            p = Path(entry.path)
            if ignore_dirname is not None and p.name == ignore_dirname:
                continue
            todo_dirs.append(p)

    return dirs


def _bootstrap_project_dirs(
    invoc_dir: Path,
    project_dir: Path,
    dirname: Optional[str],
    force: bool,
) -> Path:

    project_dir = (
        project_dir / (dirname or ".")
        if dirname is not None and not os.path.isabs(dirname)
        else Path(dirname or ".")
    ).resolve()

    if not force and project_dir.exists() and any(True for _ in project_dir.iterdir()):
        raise err.VoltCliError(
            f"project directory {project_dir} contains files -- use the `-f` flag to"
            " force creation in nonempty directories"
        )

    config = Config(invoc_dir=invoc_dir, project_dir=project_dir)
    for dp in (
        config.sources_dir,
        config.static_dir,
        config.themes_dir,
    ):
        dp.mkdir(parents=True, exist_ok=True)

    return project_dir


def _infer_lang() -> Optional[str]:
    lang_code, _ = getlocale()
    if lang_code is None:
        return None
    try:
        lang, _ = lang_code.split("_", 1)
    except ValueError:
        return None
    return lang


def _infer_author(stdout_encoding: str = "utf-8") -> Optional[str]:
    git_exe = "git"
    if which(git_exe) is None:
        return None

    proc = _run_process([git_exe, "config", "--get", "user.name"])
    if proc.returncode != 0:
        return None

    author = proc.stdout.strip().decode(stdout_encoding) or None

    return author


def _infer_front_matter(query: str, title: Optional[str]) -> str:
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


def _initialize_git(project_dir: Path, stream_encoding: str = "utf-8") -> bool:
    git_exe = "git"
    if which(git_exe) is None:
        log.debug("can not find 'git' executable")
        return False

    proc_init = _run_process(["git", "-C", f"{project_dir}", "init"])
    if proc_init.returncode != 0:
        log.debug(
            "git init failed",
            stdout=proc_init.stdout.decode(stream_encoding),
            stderr=proc_init.stderr.decode(stream_encoding),
        )
        return False

    proc_add = _run_process(["git", "-C", f"{project_dir}", "add", f"{project_dir}"])
    if proc_add.returncode != 0:
        log.debug(
            "git add failed",
            stdout=proc_add.stdout.decode(stream_encoding),
            stderr=proc_add.stderr.decode(stream_encoding),
        )
        return False

    return True


def _run_process(toks: list[str]) -> sp.CompletedProcess:
    return sp.run(toks, capture_output=True)
