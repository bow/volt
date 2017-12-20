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

import click
import toml
from jinja2 import Environment, FileSystemLoader

from . import __version__
from .config import SessionConfig, CONFIG_FNAME
from .site import Site
from .utils import get_tz, find_pwd, Result

__all__ = []


class Session(object):

    """Representation of a CLI session."""

    @classmethod
    def do_init(cls, target_wd, name, url, timezone, force,
                config_fname=CONFIG_FNAME):
        """Creates directories and files for a new site.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :returns: Error messages as a list of strings.

        """
        try:
            target_wd.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        if not force and any(True for _ in target_wd.iterdir()):
            return Result.as_failure(
                "target project directory is not empty -- use the `-f` flag to"
                " force init in nonempty directories")

        rtz = get_tz(timezone)
        if rtz.is_failure:
            return rtz

        # Bootstrap directories.
        bootstrap_conf = SessionConfig(target_wd, timezone=rtz.data).site
        try:
            bootstrap_conf.contents_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.templates_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.static_src.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        # Create initial TOML config file.
        init_conf = OrderedDict([
            ("site", OrderedDict([
                ("name", name),
                ("url", url),
                ("timezone", rtz.data.zone),
            ]))
        ])
        target_wd.joinpath(config_fname).write_text(toml.dumps(init_conf))

        return Result.as_success(None)

    @classmethod
    def do_build(cls, start_lookup_dir=None, clean_dest=True):
        """Builds the site."""
        rpwd = find_pwd(CONFIG_FNAME, start_lookup_dir)
        if rpwd.is_failure:
            return rpwd

        rsc = SessionConfig.from_toml(rpwd.data, CONFIG_FNAME)
        if rsc.is_failure:
            return rsc

        session_config = rsc.data
        # TODO: wipe and write only the necessary ones
        site_dest = session_config.site.site_dest
        if clean_dest:
            with suppress(FileNotFoundError):
                shutil.rmtree(str(site_dest))
            site_dest.mkdir(parents=True)

        env = Environment(
            loader=FileSystemLoader(str(session_config.site.templates_src)),
            auto_reload=False,
            enable_async=True)
        site = Site(session_config, env)
        rbuild = site.build()
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
                   " the created config file. Default: empty string.")
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
def init(ctx, name, url, project_dir, timezone, force):
    """Initializes a new Volt project."""
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
def build(ctx, project_dir, clean):
    _, errs = Session.do_build(project_dir, clean)
    if errs:
        raise click.UsageError(errs)
