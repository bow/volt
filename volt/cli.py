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
from os import path
from pathlib import Path
from typing import Optional

import click
import toml
from jinja2 import Environment, FileSystemLoader

from . import __version__
from .config import SiteConfig, CONFIG_FNAME
from .site import Site
from .utils import get_tz, find_pwd, Result

__all__ = []


class Session(object):

    """Commands for a single CLI session."""

    @staticmethod
    def do_init(pwd: Path, name: str, url: str, timezone: str, force: bool,
                config_fname: str=CONFIG_FNAME) -> Result[None]:
        """Initializes a new project.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :param pathlib.path pwd: Path to the project directory to be created.
        :param str name: Name of the static site, to be put inside the
            generated config file.
        :param str url: URL of the static site, to be put inside the generated
            config file.
        :param str timezone: Geographical timezone name for timestamp-related
            values, to be put inside the generated config file.
        :param bool force: Whether to force project creation in nonempty
            directories or not.
        :param str config_name: Name of the config file to generate.
        :returns: Nothing upon successful execution or an error message when
            execution fails.
        :rtype: :class:`Result`.

        """
        try:
            pwd.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        if not force and any(True for _ in pwd.iterdir()):
            return Result.as_failure(
                "target project directory is not empty -- use the `-f` flag to"
                " force init in nonempty directories")

        rtz = get_tz(timezone)
        if rtz.is_failure:
            return rtz

        # Bootstrap directories.
        bootstrap_conf = SiteConfig(pwd, timezone=rtz.data)
        try:
            bootstrap_conf.contents_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.templates_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.assets_src.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        # Create initial TOML config file.
        init_conf = OrderedDict([
            ("site", OrderedDict([
                ("name", name or ""),
                ("url", url or ""),
                ("timezone", rtz.data.zone),
            ]))
        ])
        pwd.joinpath(config_fname).write_text(toml.dumps(init_conf))

        return Result.as_success(None)

    @staticmethod
    def do_build(cwd: Path, start_lookup_dir: Optional[str]=None,
                 clean_dest: bool=True) -> Result[None]:
        """Builds the static site.

        This function may overwrite and/or remove any preexisting files
        and or directories.

        :param pathlib.Path cwd: Path to the directory from which the command
            was invoked.
        :param str start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param bool clean_dest: Whether to remove the entire site output
            directory prior to building, or not.
        :returns: Nothing upon successful execution or an error message when
            execution fails.
        :rtype: :class:`Result`.

        """
        rpwd = find_pwd(CONFIG_FNAME, start_lookup_dir)
        if rpwd.is_failure:
            return rpwd

        rsc = SiteConfig.from_toml(rpwd.data, CONFIG_FNAME)
        if rsc.is_failure:
            return rsc

        site_config = rsc.data
        # TODO: wipe and write only the necessary ones
        site_dest = site_config.site_dest
        if clean_dest:
            with suppress(FileNotFoundError):
                shutil.rmtree(str(site_dest))
            site_dest.mkdir(parents=True)

        env = Environment(
            loader=FileSystemLoader(str(site_config.templates_src)),
            auto_reload=False,
            enable_async=True)
        site = Site(site_config, env)
        rbuild = site.build(cwd)
        if rbuild.is_failure:
            return rbuild

        return Result.as_success(None)


@click.group()
@click.version_option(__version__)
@click.option("-l", "--log-level",
              type=click.Choice(["debug", "info", "warning", "error",
                                 "critical"]),
              default="info",
              help="Logging level. Default: 'info'.")
@click.pass_context
def main(ctx, log_level):
    """A versatile static website generator"""
    ctx.params["log_level"] = log_level


@main.command()
@click.argument("project_dir",
                type=click.Path(exists=False, dir_okay=True, readable=True,
                                resolve_path=True),
                required=False)
@click.option("-n", "--name", type=str, required=False, default="",
              help="Name of the Volt site. If given, the value will be set in"
                   " the created config file. Default: empty string or the"
                   " value of `project_dir`, when available.")
@click.option("-u", "--url", type=str, required=False, default="",
              help="URL of the Volt site. If given, the value will be set in"
                   " the created config file. Default: empty string.")
@click.option("-z", "--timezone", type=str, required=False, default=None,
              help="Geographical timezone name for interpreting timestamps."
                   " Default: system timezone.")
@click.option("-f", "--force", is_flag=True,
              help="If set, volt may overwrite any files and/or directories"
                   " in the init directory. Otherwise, init will fail if any"
                   " files and/or directories exist in the target directory.")
@click.pass_context
def init(ctx, project_dir: str, name: Optional[str], url: Optional[str],
         timezone: Optional[str], force: bool):
    """Initializes a new project.

    Project initialization consists of:

        1. Creating the project directory and directories for contents,
           templates, and assets, inside the project directory.

        2. Creating the configuration file.

    If no project directory is specified, this command defaults to
    initialization in the current directory.

    """
    pwd = Path.cwd() if project_dir is None else Path.cwd().joinpath(
        project_dir)
    name = path.basename(project_dir) \
        if (not name and project_dir is not None) else name

    _, errs = Session.do_init(pwd, name, url, timezone, force)
    if errs:
        raise click.UsageError(errs)
    # TODO: add message for successful init


@main.command()
@click.argument("project_dir",
                type=click.Path(exists=True, dir_okay=True, file_okay=False,
                                readable=True, writable=True),
                required=False)
@click.option("-c", "--clean", is_flag=True, default=True,
              help="If set, Volt will remove the target site directory prior"
                   " to site creation. Default: set.")
@click.pass_context
def build(ctx, project_dir: Optional[str], clean: bool):
    """Builds the static site.

    This command generates the static site in the site destination directory
    (default: `site`).

    If no project directory is specified, this command will start lookup of the
    project directory from the current directory upwards. If a project
    directory is specified, no repeated lookups will be performed.

    """
    _, errs = Session.do_build(Path.cwd(), project_dir, clean)
    if errs:
        raise click.UsageError(errs)
