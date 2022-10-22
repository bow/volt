"""Functions invoked in a single execution session."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import os
import time
from contextlib import suppress
from pathlib import Path
from typing import Optional

import click
import pendulum
import structlog

from . import constants, exceptions as excs
from .config import Config
from .server import Rebuilder, make_server
from .site import Site
from .utils import (
    get_fuzzy_match,
    infer_author,
    infer_front_matter,
    infer_lang,
)

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
    :param config_name: Name of the config file to generate.

    :raises ~volt.exceptions.VoltCliError:
        * when the given project directory is not empty and force is False.
        * when any directory creation fails.

    """
    project_dir = (
        project_dir.resolve() / (dirname or ".")
        if dirname is not None and not os.path.isabs(dirname)
        else Path(dirname or ".")
    )
    if not name and dirname is not None:
        name = project_dir.name
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise excs.VoltCliError(e.strerror) from e

    if not force and any(True for _ in project_dir.iterdir()):
        raise excs.VoltCliError(
            f"project directory {project_dir} contains files -- use the `-f` flag to"
            " force creation in nonempty directories"
        )

    # Bootstrap directories.
    config = Config(invoc_dir=invoc_dir, project_dir=project_dir)
    for dp in (
        config.sources_dir,
        config.static_dir,
        config.themes_dir,
    ):
        try:
            dp.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise excs.VoltCliError(e.strerror) from e

    # Create initial YAML config file.
    new_conf = f"""---
# Volt configuration file.
name: "{name}"
url: "{url}"
description: "{description}"
author: "{author or (infer_author() or '')}"
language: "{language or (infer_lang() or '')}"
"""

    # Create initial YAML config file.
    (project_dir / config_fname).write_text(new_conf)

    return project_dir


def build(
    config: Config,
    clean: bool = True,
    with_drafts: bool = False,
) -> Site:
    """Build the site.

    This function may overwrite and/or remove any preexisting files
    and or directories.

    :param config: Site configuration.
    :param clean: Whether to remove the entire site output directory prior
        to building, or not.

    """
    config._with_drafts = with_drafts

    start_time = time.monotonic()
    config["build_time"] = pendulum.now()

    site = Site(config=config)
    site.build(clean=clean)

    log.info("build completed", duration=f"{(time.monotonic() - start_time):.2f}s")

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
            text=infer_front_matter(query, title),
            extension=constants.MARKDOWN_EXT,
            require_save=False,
        )
        if contents:
            log.info(
                f"created new draft at {str(new_fp.relative_to(config.invoc_dir))!r}"
            )
            new_fp.write_text(contents)

        return None

    match_fp = get_fuzzy_match(
        query=query,
        ext=constants.MARKDOWN_EXT,
        start_dir=config.sources_dir,
        ignore_dirname=None if lookup_drafts else config.drafts_dirname,
    )
    if match_fp is not None:
        click.edit(filename=f"{match_fp}")
        return None

    raise excs.VoltResourceError(f"found no matching file for {query!r}")


def serve(
    config: Config,
    host: Optional[str],
    port: int,
    do_build: bool,
    build_with_drafts: bool,
    build_clean: bool,
) -> None:

    eff_host = "127.0.0.1"
    if host is not None:
        eff_host = host
    elif config.in_docker:
        eff_host = "0.0.0.0"

    serve = make_server(config, eff_host, port)

    if do_build:

        def builder() -> None:
            nonlocal config
            try:
                # TODO: Only reload config post-init, on config file change.
                config = config.reload()
                build(config, build_clean, build_with_drafts)
            except Exception as e:
                msg = "build failed"
                build_exists = False
                target_dir = config.target_dir
                with suppress(Exception):
                    if target_dir.exists() and any(True for _ in target_dir.iterdir()):
                        build_exists = True
                if build_exists:
                    msg += " -- keeping current build"
                log.error(msg)
                log.exception(e)
                return None
            return None

        with Rebuilder(config, builder):
            builder()
            log.debug("starting dev server")
            serve()
    else:
        serve()
