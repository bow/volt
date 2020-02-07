# -*- coding: utf-8 -*-
"""
    volt.cli
    ~~~~~~~~

    Main entry point for command line invocation.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import shutil
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from typing import Optional

import click
import toml

from . import __version__
from .config import CONFIG_FNAME, SiteConfig
from .site import Site
from .utils import Result, find_pwd, get_tz


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
        config_fname: str = CONFIG_FNAME,
    ) -> Result[None]:
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

        :returns: Nothing upon successful execution or an error message when
            execution fails.

        """
        name = pwd.name if (not name and pwd is not None) else name
        pwd = cwd if pwd is None else cwd.joinpath(pwd)
        try:
            pwd.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        if not force and any(True for _ in pwd.iterdir()):
            return Result.as_failure(
                "target project directory is not empty -- use the `-f` flag to"
                " force init in nonempty directories"
            )

        rtz = get_tz(timezone)
        if rtz.is_failure:
            return rtz

        # Bootstrap directories.
        bootstrap_conf = SiteConfig(cwd, pwd, timezone=rtz.data)
        try:
            for dk in ("contents_src", "templates_src", "assets_src"):
                bootstrap_conf[dk].mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        # Create initial TOML config file.
        init_conf = OrderedDict([
            (
                "site", OrderedDict([
                    ("name", name or ""),
                    ("url", url or ""),
                    ("timezone", rtz.data.zone),
                ]),
            ),
        ])
        pwd.joinpath(config_fname).write_text(toml.dumps(init_conf))

        return Result.as_success(None)

    @staticmethod
    def do_build(
        cwd: Path,
        start_lookup_dir: Optional[Path] = None,
        clean: bool = True,
    ) -> Result[None]:
        """Build the static site.

        This function may overwrite and/or remove any preexisting files
        and or directories.

        :param cwd: Path to the directory from which the command was invoked.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param clean: Whether to remove the entire site output directory prior
            to building, or not.

        :returns: Nothing upon successful execution or an error message when
            execution fails.

        """
        rpwd = find_pwd(CONFIG_FNAME, start_lookup_dir)
        if rpwd.is_failure:
            return rpwd

        rsc = SiteConfig.from_toml(cwd, rpwd.data, CONFIG_FNAME)
        if rsc.is_failure:
            return rsc

        site_config = rsc.data
        with suppress(FileNotFoundError):
            if clean:
                # TODO: wipe and write only the necessary ones
                shutil.rmtree(str(site_config["site_dest"]))

        site = Site(site_config)
        rbuild = site.build()
        if rbuild.is_failure:
            return rbuild

        return Result.as_success(None)


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
        "Name of the Volt site. If given, the value will be set in the created"
        " config file. Default: empty string or the value of `project_dir`,"
        " when available."
    )
)
@click.option(
    "-u",
    "--url",
    type=str,
    required=False,
    default="",
    help=(
        "URL of the Volt site. If given, the value will be set in the created"
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
    """Initialize a new project.

    Project initialization consists of:

        1. Creating the project directory and directories for contents,
           templates, and assets, inside the project directory.

        2. Creating the configuration file.

    If no project directory is specified, this command defaults to
    initialization in the current directory.

    """
    pwd = Path(project_dir) if project_dir is not None else project_dir
    _, errs = Session.do_init(Path.cwd(), pwd, name, url, timezone, force)
    if errs:
        raise click.UsageError(errs)
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
    """Build the static site.

    This command generates the static site in the site destination directory
    (default: `site`).

    If no project directory is specified, this command will start lookup of the
    project directory from the current directory upwards. If a project
    directory is specified, no repeated lookups will be performed.

    """
    _, errs = Session.do_build(
        Path.cwd(),
        Path(project_dir) if project_dir is not None else None,
        clean,
    )
    if errs:
        raise click.UsageError(errs)
