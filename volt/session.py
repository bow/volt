"""Functions invoked in a single execution session."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import bdb
import os
import subprocess as sp
import time
from contextlib import suppress
from locale import getlocale
from pathlib import Path
from shutil import copytree, which
from typing import Optional

import pendulum
import structlog
import tomlkit
from structlog.contextvars import bound_contextvars

from . import constants, error as err
from .config import Config, _VCS
from .server import _Rebuilder, _RunFile, make_server
from .site import Site


__all__ = ["build", "new", "serve"]


log = structlog.get_logger(__name__)


def new(
    dir_name: Optional[str],
    invoc_dir: Path,
    project_dir: Path,
    name: str,
    url: str,
    authors: list[str],
    description: Optional[str],
    language: Optional[str],
    force: bool,
    theme: Optional[str],
    vcs: Optional[_VCS],
    config_file_name: str = constants.CONFIG_FILE_NAME,
) -> Path:
    """Create a new project.

    This function may overwrite any preexisting files and or directories
    in the target working directory.

    :param dir_name: Name of the directory in which the project is created.
    :param invoc_dir: Path to the invocation directory.
    :param project_dir: Path to the parent directory in which ``dir_name`` is created.
    :param name: Name of the static site, to be put inside the generated config file.
    :param url: URL of the static site, to be put inside the generated config file.
    :param description: Description of the site, to be put inside the generated
        config file.
    :param description: Language of the site, to be put inside the generated
        config file. If set to ``None``, the value will be inferred from the system
        locale.
    :param force: Whether to force project creation in nonempty directories or not.
    :param vcs: Version control system to initialize in the newly created project.
    :param theme: Name of theme to include.
    :param config_file_name: Name of the config file to generate.

    :raises ~volt.error.VoltCliError:
        * when the given project directory is not empty and force is False.
        * when any directory creation fails.

    """
    project_dir = _resolve_project_dir(invoc_dir, project_dir, dir_name, force)

    file_config = _resolve_file_config(
        project_dir=project_dir,
        name=name,
        url=url,
        theme=theme,
        description=description,
        authors=authors,
        language=language,
        dir_name_specified=dir_name is not None,
    )

    config = Config(
        invoc_dir=invoc_dir,
        project_dir=project_dir,
        user_conf={"theme": {"name": theme}},
    )
    for dp in (
        config.sources_dir,
        config.static_dir,
        config.themes_dir,
    ):
        dp.mkdir(parents=True, exist_ok=True)
    with (project_dir / config_file_name).open("w") as fh:
        fh.write("# Volt configuration file\n\n")
        tomlkit.dump(file_config, fh, sort_keys=False)

    if (tn := config.theme_name) is not None:
        theme_src_dir = Path(__file__).parent / "themes" / tn
        copytree(src=theme_src_dir, dst=config.themes_dir / tn, dirs_exist_ok=False)
        (config.sources_dir / "index.md").write_text("# My First Page\nHello, World")

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
                raise ValueError(f"vcs {vcs!r} is unsupported")

    return project_dir


def build(config: Config, clean: bool = True) -> Optional[Site]:
    """Build the site.

    This function may overwrite and/or remove any preexisting files
    and or directories.

    :param config: Site configuration.
    :param clean: Whether to remove the entire site output directory prior
        to building, or not.

    """
    site: Optional[Site] = None

    start_time = time.monotonic()
    config["build_time"] = pendulum.now()

    with bound_contextvars(drafts=config.with_drafts):
        try:
            site = Site(config)
            site.build(clean=clean)
            log.info(
                "build completed",
                duration=f"{(time.monotonic() - start_time):.2f}s",
            )
        except bdb.BdbQuit:
            log.warn("exiting from debugger -- build may be compromised")
        except Exception:
            msg = "build failed"
            target_dir = config.target_dir
            with suppress(Exception):
                if target_dir.exists() and any(True for _ in target_dir.iterdir()):
                    msg += " -- keeping current build"
            log.error(msg)
            raise

    return site


def serve(
    config: Config,
    host: Optional[str],
    port: int,
    watch: bool,
    pre_build: bool,
    build_clean: bool,
    log_level: str,
    with_sig_handlers: bool,
) -> None:

    eff_host = "127.0.0.1"
    if host is not None:
        eff_host = host
    elif config.in_docker:
        eff_host = "0.0.0.0"

    build_with_drafts = config.with_drafts
    serve = make_server(config, eff_host, port, log_level, with_sig_handlers)

    if not watch:
        serve()

    else:

        def builder() -> None:
            nonlocal config
            rf = _RunFile.from_path(config._server_run_path)
            drafts = build_with_drafts if rf is None else rf.drafts
            try:
                # TODO: Only reload config post-init, on config file change.
                config = config.reload(drafts=drafts)
                build(config, build_clean)
            except Exception as e:
                log.exception(e)

        with _Rebuilder(config, builder):
            if pre_build:
                builder()
            log.debug("starting dev server")
            serve()


def serve_drafts(config: Config, value: Optional[bool]) -> None:
    rf = _RunFile.from_path(config._server_run_path)
    if rf is None:
        # NOTE: Setting 'drafts' to False here since we will toggle it later.
        rf = _RunFile.from_config(config=config, drafts=False)

    return rf.toggle_drafts(value).dump()


def _resolve_project_dir(
    invoc_dir: Path,
    project_dir: Path,
    dir_name: Optional[str],
    force: bool,
) -> Path:

    dir_name_specified = dir_name is not None
    dir_name_abs = dir_name is not None and os.path.isabs(dir_name)
    project_dir_specified = invoc_dir != project_dir

    if dir_name_specified and dir_name_abs and project_dir_specified:
        log.warn(
            "ignoring specified project path as command is invoked with an absolute"
            " path",
            project_path=project_dir,
            command_path=dir_name,
        )

    project_dir = (project_dir / (dir_name or ".")).resolve()

    project_dir_nonempty = project_dir.exists() and any(
        True for _ in project_dir.iterdir()
    )

    if not force and project_dir_nonempty:
        raise err.VoltCliError(
            f"project directory {project_dir} contains files -- use the `-f` flag to"
            " force creation in nonempty directories"
        )

    return project_dir


def _resolve_file_config(
    project_dir: Path,
    name: str,
    url: str,
    theme: Optional[str],
    description: Optional[str],
    authors: list[str],
    language: Optional[str],
    dir_name_specified: bool,
) -> dict:

    if not name and dir_name_specified:
        name = project_dir.name

    site_config: dict[str, str | list[str]] = {
        "name": name.capitalize(),
        "url": url,
    }

    if description is not None:
        site_config["description"] = description

    if not authors:
        if (author := _infer_author()) is not None:
            authors.append(author)
    site_config["authors"] = authors

    if lang := language or (_infer_lang() or ""):
        site_config["language"] = lang

    config = {"site": site_config}

    if theme is not None:
        config["theme"] = {"name": theme}

    return config


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
    if (git_exe := which("git")) is None:
        return None

    proc = _run_process([git_exe, "config", "--get", "user.name"])
    if proc.returncode != 0:
        log.warn("no author can be inferred as git returns no 'user.name' value")
        return None

    author = proc.stdout.strip().decode(stdout_encoding) or None

    return author


def _infer_front_matter(query: str, title: Optional[str]) -> str:
    fm = {}
    default_title = Path(query).stem

    title = " ".join([tok.capitalize() for tok in (title or default_title).split("-")])
    fm["title"] = title

    strv = "\n".join([f"{k}: {v}" for k, v in fm.items()])

    return f"""---\n{strv}\n---"""


def _initialize_git(project_dir: Path, stream_encoding: str = "utf-8") -> bool:

    gitignore = project_dir / ".gitignore"
    gitignore.write_text(f"# Volt server run file\n{constants.SERVER_RUN_FILE_NAME}")

    if (git_exe := which("git")) is None:
        log.warn("can not find git executable")
        return False

    proc_init = _run_process([git_exe, "-C", f"{project_dir}", "init"])
    if proc_init.returncode != 0:
        log.warn(
            "git init failed",
            stdout=proc_init.stdout.decode(stream_encoding),
            stderr=proc_init.stderr.decode(stream_encoding),
        )
        return False

    proc_add = _run_process([git_exe, "-C", f"{project_dir}", "add", "."])
    if proc_add.returncode != 0:
        log.warn(
            "git add failed",
            stdout=proc_add.stdout.decode(stream_encoding),
            stderr=proc_add.stderr.decode(stream_encoding),
        )
        return False

    return True


def _run_process(toks: list[str]) -> sp.CompletedProcess:
    return sp.run(toks, capture_output=True)
