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
from .config import SiteConfig
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
@click.option("-c", "--config-path",
              type=click.Path(exists=True, dir_okay=False, readable=True,
                              resolve_path=True),
              help="Path to a volt config file. If not supplied, volt will"
                   " use its default settings for initialization. If supplied,"
                   " init will also use the configuration values.")
@click.option("-f", "--force", is_flag=True,
              help="If set, volt may overwrite any files and/or directories"
                   " in the init directory. Otherwise, init will fail if any"
                   " other files and/or directories (except for the config"
                   " file that may be set with `--config`) exist in the init"
                   " directory.")
@click.pass_context
def init(ctx, config_path, force):
    """Initializes a new volt site"""
    work_path = Path()
    expected = {config_path} if config_path is not None else {}
    unexpected = (i for i in work_path.iterdir()
                  if not force and str(i.absolute()) not in expected)
    # We're actually only interested in the first item, which will
    # always raise and exception if it exist. The for-loop is just so
    # that we don't load all the unecessary directory contents first.
    for _ in unexpected:
        raise click.UsageError("work directory is not empty --"
                               " use the `-f` flag to force init in nonempty"
                               " directories")

    config = SiteConfig(work_path)
    if config_path is not None:
        config, errors = config.update_with_toml(config_path)
        for error in errors:
            raise click.UsageError(error)

    site = Site(config)

    errors = site.run_init(config_path is None)
    for error in errors:
        raise click.UsageError(error)
    # TODO: add message for successful init
