# -*- coding: utf-8 -*-
"""
    volt.cli
    ~~~~~~~~

    Main entry point for command line invocation.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from collections import OrderedDict
from pathlib import Path

import click
import toml

from . import __version__
from .config import SessionConfig, CONFIG_FNAME
from .utils import Result

__all__ = []


class Session(object):

    """Representation of a CLI session."""

    @classmethod
    def do_init(cls, target_wd, name, url, force, config_fname=CONFIG_FNAME):
        """Creates directories and files for a new site.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :returns: Error messages as a list of strings.

        """
        try:
            target_wd.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        try:
            next(target_wd.iterdir())
        except StopIteration:
            pass
        else:
            if not force:
                return Result.as_failure(
                    "target project directory is not empty -- use the `-f`"
                    " flag to force init in nonempty directories")

        # Bootstrap directories.
        bootstrap_conf = SessionConfig(target_wd).site
        try:
            bootstrap_conf.contents_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.templates_src.mkdir(parents=True, exist_ok=True)
            bootstrap_conf.assets_src.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return Result.as_failure(e.strerror)

        # Create initial TOML config file.
        init_conf = OrderedDict([
            ("site", OrderedDict([
                ("name", name),
                ("url", url),
            ]))
        ])
        target_wd.joinpath(config_fname).write_text(toml.dumps(init_conf))

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
@click.option("-f", "--force", is_flag=True,
              help="If set, volt may overwrite any files and/or directories"
                   " in the init directory. Otherwise, init will fail if any"
                   " files and/or directories exist in the target directory.")
@click.pass_context
def init(ctx, name, url, project_dir, force):
    """Initializes a new Volt project."""
    pwd = Path.cwd() if project_dir is None else Path.cwd().joinpath(
        project_dir)
    _, errs = Session.do_init(pwd, name, url, force)
    if errs:
        raise click.UsageError(errs.pop())
    # TODO: add message for successful init
