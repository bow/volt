"""Functions invoked in a single execution session."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import os
import time
import traceback
from pathlib import Path
from typing import Optional

import click
import pendulum

from . import constants, exceptions as excs
from .config import SiteConfig
from .server import Rebuilder, make_server
from .site import Site
from .utils import (
    echo_err,
    echo_info,
    get_fuzzy_match,
    infer_author,
    infer_front_matter,
    infer_lang,
)


def new(
    dirname: Optional[str],
    cwd: Path,
    pwd: Path,
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
    :param cwd: Path to the invocation directory.
    :param pwd: Path to the parent directory in which ``dirname`` is created.
    :param name: Name of the static site, to be put inside the generated config
        file.
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
    pwd = (
        pwd.resolve() / (dirname or ".")
        if dirname is not None and not os.path.isabs(dirname)
        else Path(dirname or ".")
    )
    if not name and dirname is not None:
        name = pwd.name
    try:
        pwd.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise excs.VoltCliError(e.strerror) from e

    if not force and any(True for _ in pwd.iterdir()):
        raise excs.VoltCliError(
            f"project directory {pwd} contains files -- use the `-f` flag to"
            " force creation in nonempty directories"
        )

    # Bootstrap directories.
    config = SiteConfig(cwd=cwd, pwd=pwd)
    for dp in (
        config.sources_path,
        config.static_path,
        config.themes_path,
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
    (pwd / config_fname).write_text(new_conf)

    return pwd


def build(
    sc: SiteConfig,
    clean: bool = True,
    with_drafts: bool = False,
) -> Site:
    """Build the site.

    This function may overwrite and/or remove any preexisting files
    and or directories.

    :param site_config: Site configuration.
    :param clean: Whether to remove the entire site output directory prior
        to building, or not.

    """
    sc._with_drafts = with_drafts

    start_time = time.monotonic()
    sc["build_time"] = pendulum.now()

    site = Site(config=sc)
    site.build(clean=clean)
    echo_info(
        f"build"
        f"{'' if not with_drafts else ' with drafts'}"
        f" completed in {(time.monotonic() - start_time):.2f}s"
    )

    return site


def edit(
    sc: SiteConfig,
    query: str,
    create: Optional[str] = None,
    title: Optional[str] = None,
    lookup_drafts: bool = False,
) -> None:
    """Open a draft file in an editor."""

    if create is not None:
        fn = Path(sc.drafts_dirname) / create / query
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
            echo_info(f"created new draft at {str(new_fp.relative_to(sc.cwd))!r}")
            new_fp.write_text(contents)

        return None

    match_fp = get_fuzzy_match(
        query=query,
        ext=constants.MARKDOWN_EXT,
        start_dir=sc.sources_path,
        ignore_dirname=None if lookup_drafts else sc.drafts_dirname,
    )
    if match_fp is not None:
        click.edit(filename=f"{match_fp}")
        return None

    raise excs.VoltResourceError(f"found no matching file for {query!r}")


def serve(
    sc: SiteConfig,
    host: Optional[str],
    port: int,
    do_build: bool,
    build_with_drafts: bool,
    build_clean: bool,
) -> None:

    eff_host = "127.0.0.1"
    if host is not None:
        eff_host = host
    elif sc.in_docker:
        eff_host = "0.0.0.0"

    serve = make_server(sc, eff_host, port)

    if do_build:

        rebuild_count = 0

        def builder() -> None:
            nonlocal sc, rebuild_count
            if rebuild_count > 0:
                echo_info("detected source change -- rebuilding")
            try:
                # TODO: Only reload config post-init, on config file change.
                sc = sc.reload()
                build(sc, build_clean, build_with_drafts)
            except click.ClickException as e:
                e.show()
                echo_err("new build failed -- keeping current build")
                return None
            except Exception as e:
                echo_err("new build failed -- keeping current build")
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                echo_err("".join(tb))
                return None
            finally:
                rebuild_count += 1
            return None

        with Rebuilder(sc, builder):
            echo_info(
                f"starting dev server"
                f"{'' if not build_with_drafts else ' in drafts mode'}"
                " with rebuilder"
            )
            builder()
            serve()
    else:
        serve()
