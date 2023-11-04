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
from click import style
from structlog.contextvars import bound_contextvars

from . import constants, error as err
from .config import Config, _VCS
from .server import _Rebuilder, _RunFile, make_server
from .theme import Theme
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
    in the target directory path.

    :param dir_name: Name of the directory in which the project is created.
    :param invoc_dir: Path to the invocation directory.
    :param project_dir: Path to the parent directory in which ``dir_name`` is created.
    :param name: Name of the static site, to be put inside the generated config file.
    :param url: URL of the static site, to be put inside the generated config file.
    :param description: Description of the site, to be put inside the generated
        config file.
    :param language: Language of the site, to be put inside the generated
        config file. If set to ``None``, the value will be inferred from the system
        locale.
    :param force: Whether to force project creation in nonempty directories or not.
    :param theme: Name of theme to include.
    :param vcs: Version control system to initialize in the newly created project.
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
        user_conf={"theme": {"source": theme}},
    )
    for dp in (
        config.contents_dir,
        config.static_dir,
        config.themes_dir,
    ):
        dp.mkdir(parents=True, exist_ok=True)
    with (project_dir / config_file_name).open("w") as fh:
        fh.write("# volt configuration file\n\n")
        tomlkit.dump(file_config, fh, sort_keys=False)

    if (tn := config.theme_source) is not None:
        theme_src_dir = Path(__file__).parent / "themes" / tn
        copytree(src=theme_src_dir, dst=config.themes_dir / tn, dirs_exist_ok=False)
        (config.contents_dir / "index.md").write_text("# My First Page\nHello, World")

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


def build(config: Config, with_draft: bool, clean: bool) -> Optional[Site]:
    """Build the site.

    This function may overwrite and/or remove any preexisting files
    and or directories.

    :param config: Site configuration.
    :param with_draft: Whether draft contents are included in the build or not.
    :param clean: Whether to remove the entire site output directory prior
        to building, or not.

    """
    site: Optional[Site] = None

    start_time = time.monotonic()
    config["build_time"] = pendulum.now()

    with bound_contextvars(with_draft=with_draft):
        try:
            site = Site(config)
            site.build(with_draft=with_draft, clean=clean)
            log.info(
                "build completed",
                duration=f"{(time.monotonic() - start_time):.2f}s",
            )
        except bdb.BdbQuit:
            log.warn("exiting from debugger -- build may be compromised")
        except Exception:
            msg = "build failed"
            output_dir = config.output_dir
            with suppress(Exception):
                if output_dir.exists() and any(True for _ in output_dir.iterdir()):
                    msg += " -- keeping current build"
            log.error(msg)
            raise

    return site


def serve(
    config: Config,
    host: Optional[str],
    port: int,
    with_draft: bool,
    open_browser: bool,
    watch: bool,
    build_clean: bool,
    pre_build: bool,
    with_sig_handlers: bool,
    log_level: str,
    log_color: bool,
) -> None:
    eff_host = "127.0.0.1"
    if host is not None:
        eff_host = host
    elif config.in_docker:
        eff_host = "0.0.0.0"

    serve = make_server(
        config=config,
        host=eff_host,
        port=port,
        with_draft=with_draft,
        with_sig_handlers=with_sig_handlers,
        log_level=log_level,
        log_color=log_color,
    )

    if not watch:
        serve(open_browser)

    else:

        def builder() -> None:
            nonlocal config
            rf = _RunFile.from_path(config._server_run_path)
            draft = with_draft if rf is None else rf.draft
            try:
                # TODO: Only reload config post-init, on config file change.
                config = config.reload()
                build(config, with_draft=draft, clean=build_clean)
            except Exception as e:
                log.exception(e)

        with _Rebuilder(config, builder):
            if pre_build:
                builder()
            log.debug("starting dev server")
            serve(open_browser)


def serve_draft(config: Config, value: Optional[bool]) -> None:
    rf = _RunFile.from_path(config._server_run_path)
    if rf is None:
        # NOTE: Setting 'draft' to False here since we will toggle it later.
        rf = _RunFile.from_config(config=config, draft=False)

    return rf.toggle_draft(value).dump()


def theme_show(config: Config, with_color: bool) -> None:
    theme = Theme.from_config(config)
    path = theme.source.path.relative_to(  # type: ignore[call-arg]
        config.invoc_dir,
        walk_up=True,
    )
    name = theme.name or "<unnamed-theme>"

    info_lines: list[str]
    if with_color:
        name_v = style(f" {name} ", fg="black", bg="cyan", bold=True)
        path_v = style(f"{path}", fg="bright_black")
        desc_v = (
            style(f"{theme.description}", fg="yellow")
            if theme.description is not None
            else ""
        )
        kw = len(name)
        info_lines = [f"{name_v}"] + [
            f" • {v}"
            for v in (
                desc_v,
                path_v,
            )
            if v
        ]
    else:
        pairs = {
            k: v
            for k, v in {
                "Name": name,
                "Desc": theme.description,
                "Source": path,
            }.items()
            if v is not None
        }
        kw = max([len(k) for k in pairs])
        info_lines = [f"{k:<{kw}} : {v}" for k, v in pairs.items()]

    print("\n".join(info_lines))

    return None


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


def _initialize_git(project_dir: Path, stream_encoding: str = "utf-8") -> bool:
    gitignore = project_dir / ".gitignore"
    gitignore.write_text(f"# volt server run file\n{constants.SERVER_RUN_FILE_NAME}")

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
