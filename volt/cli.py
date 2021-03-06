# -*- coding: utf-8 -*-
"""
    volt.cli
    ~~~~~~~~

    Main entry point for command line invocation.

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
from pathlib import Path
from typing import Optional

import click
import pendulum

from . import __version__, constants
from . import exceptions as exc
from .config import SiteConfig
from .site import Site
from .utils import find_dir_containing, get_tz


class Session:

    """Commands for a single CLI session."""

    @staticmethod
    def do_init(
        cwd: Path,
        pwd: Optional[Path],
        name: Optional[str],
        url: Optional[str],
        timezone: Optional[str],
        force: bool,
        config_fname: str = constants.CONFIG_FNAME,
    ) -> None:
        """Initialize a new project.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project directory to be created.
        :param name: Name of the static site, to be put inside the generated
            config file.
        :param url: URL of the static site, to be put inside the generated
            config file.
        :param timezone: Geographical timezone name for timestamp-related
            values, to be put inside the generated config file.
        :param force: Whether to force project creation in nonempty directories
            or not.
        :param config_name: Name of the config file to generate.

        :raises ~volt.exceptions.VoltCliError:
            * when the given project directory is not empty and force is False.
            * when any directory creation fails.

        """
        name = pwd.name if (not name and pwd is not None) else name
        pwd = cwd if pwd is None else (cwd / pwd).resolve()
        try:
            pwd.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise exc.VoltCliError(e.strerror) from e

        if not force and any(True for _ in pwd.iterdir()):
            raise exc.VoltCliError(
                "target project directory is not empty -- use the `-f` flag to"
                " force init in nonempty directories"
            )

        tz = get_tz(timezone)

        # Bootstrap directories.
        bootstrap_conf = SiteConfig(cwd=cwd, pwd=pwd, timezone=tz)
        bootstrap_path_attrs = [
            "src_contents_path",
            "src_scaffold_path",
            "src_theme_path",
        ]
        try:
            for attr in bootstrap_path_attrs:
                getattr(bootstrap_conf, attr).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise exc.VoltCliError(e.strerror) from e

        # Create initial YAML config file.
        init_conf = f"""# Volt configuration file.

name: "{name or ''}"
url: "{url or ''}"
description: ""
author: ""
language: ""
timezone: "{tz.name}"
"""

        # Create initial YAML config file.
        (pwd / config_fname).write_text(init_conf)

        return None

    @staticmethod
    def do_build(
        cwd: Path,
        start_lookup_dir: Optional[Path] = None,
        clean: bool = True,
    ) -> None:
        """Build the site.

        This function may overwrite and/or remove any preexisting files
        and or directories.

        :param cwd: Path to the directory from which the command was invoked.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param clean: Whether to remove the entire site output directory prior
            to building, or not.

        """
        pwd = find_dir_containing(constants.CONFIG_FNAME, start_lookup_dir)
        if pwd is None:
            raise exc.VoltCliError("project directory not found")

        site_config = SiteConfig.from_yaml(
            cwd=cwd,
            pwd=pwd.resolve(),
            yaml_fname=constants.CONFIG_FNAME,
            build_time=pendulum.now(),
        )
        site = Site(config=site_config)
        site.build(clean=clean)

        return None


@click.group()
@click.version_option(__version__)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="Logging level. Default: 'info'.",
)
@click.pass_context
def main(ctx: click.Context, log_level: str) -> None:
    """A versatile static website generator"""
    ctx.params["log_level"] = log_level


@main.command()
@click.argument(
    "project_dir",
    type=click.Path(
        exists=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    required=False,
)
@click.option(
    "-n",
    "--name",
    type=str,
    required=False,
    default="",
    help=(
        "Name of the static site. If given, the value will be set in the"
        " created config file. Default: empty string or the value of"
        " `project_dir`, when available."
    )
)
@click.option(
    "-u",
    "--url",
    type=str,
    required=False,
    default="",
    help=(
        "URL of the site. If given, the value will be set in the created"
        " config file. Default: empty string."
    )
)
@click.option(
    "-z",
    "--timezone",
    type=str,
    required=False,
    default=None,
    help=(
        "Geographical timezone name for interpreting timestamps. Default:"
        " system timezone."
    )
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help=(
        "If set, volt may overwrite any files and/or directories in the init"
        " directory. Otherwise, init will fail if any files and/or directories"
        " exist in the target directory."
    )
)
@click.pass_context
def init(
    ctx: click.Context,
    project_dir: Optional[str],
    name: Optional[str],
    url: Optional[str],
    timezone: Optional[str],
    force: bool,
) -> None:
    """Initialize a new site project.

    Project initialization consists of:

        1. Creating the project directory and directories for contents,
           templates, and assets, inside the project directory.

        2. Creating the configuration file.

    If no project directory is specified, this command defaults to
    initialization in the current directory.

    """
    Session.do_init(
        Path.cwd(),
        Path(project_dir) if project_dir is not None else None,
        name,
        url,
        timezone,
        force,
    )
    # TODO: add message for successful init


@main.command()
@click.argument(
    "project_dir",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
    ),
    required=False,
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help=(
        "If set, the target site directory will be removed prior to site"
        " building. Default: set."
    )
)
@click.pass_context
def build(ctx: click.Context, project_dir: Optional[str], clean: bool) -> None:
    """Build static site.

    This command generates the static site in the site destination directory
    (default: `site`).

    If no project directory is specified, this command will start lookup of the
    project directory from the current directory upwards. If a project
    directory is specified, no repeated lookups will be performed.

    """
    Session.do_build(
        Path.cwd(),
        Path(project_dir) if project_dir is not None else None,
        clean,
    )
