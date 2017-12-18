# -*- coding: utf-8 -*-
"""
    volt.cli
    ~~~~~~~~

    Main entry point for command line invocation.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

import click

from . import __version__
from .site import Site

__all__ = []


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
    pwd.mkdir(parents=True, exist_ok=True)

    try:
        next(pwd.iterdir())
    except StopIteration:
        pass
    else:
        if not force:
            raise click.UsageError("target project directory is not empty --"
                                   " use the `-f` flag to force init in"
                                   " nonempty directories")

    _, errs = Site.run_init(pwd, name, url)
    if errs:
        raise click.UsageError(errs)
    # TODO: add message for successful init
