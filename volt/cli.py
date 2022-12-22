"""Main entry point for command line invocation."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import sys
from contextlib import suppress
from pathlib import Path
from platform import platform
from types import ModuleType
from typing import cast, Any, Literal, Optional

import click
import structlog
from rich.traceback import install
from structlog.contextvars import bind_contextvars

from . import __version__, session
from .config import Config, _set_exc_style, _set_use_color, _ExcStyle, _VCS
from .error import VoltCliError, _VoltServerExit
from ._import import import_file
from ._logging import init_logging


__all__ = [
    "build",
    "edit",
    "main",
    "new",
    "root",
    "serve",
    "serve_drafts",
    "xcmd",
]


log = structlog.get_logger(__name__)


def main() -> None:
    """Main entry point."""
    try:
        root()
    except Exception as e:
        log.exception(e)
        sys.exit(1)
    except _VoltServerExit as e:
        log.debug("removing server run file", path=e.run_file_path)
        with suppress(Exception):
            e.run_file_path.unlink()
    else:
        log.debug("Volt completed successfully")


# Taken from:
# https://click.palletsprojects.com/en/8.0.x/advanced/#command-aliases
class _RootGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        ctx.fail(f"too many matches: {', '.join(sorted(matches))}")

    def resolve_command(
        self,
        ctx: click.Context,
        args: list[str],
    ) -> tuple[Optional[str], Optional[click.Command], list[str]]:
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name if cmd is not None else None, cmd, args


class _ExtensionGroup(click.Group):
    @classmethod
    def import_xcmd(
        cls,
        config: Config,
    ) -> Optional[ModuleType]:
        """Import the custom, user-defined subcommands."""

        fp = config.xcmd_module_path
        if not fp.exists():
            return None

        mod = import_file(fp, config.xcmd_module_name)

        return mod

    def list_commands(self, ctx: click.Context) -> list[str]:
        config = _get_config(ctx.parent)

        if (mod := self.import_xcmd(config)) is None:
            return []

        rv = [
            name
            for attr in dir(mod)
            if (
                isinstance(v := getattr(mod, attr, None), click.Command)
                and (name := v.name) is not None
            )
        ]
        rv.sort()

        return rv

    def get_command(self, ctx: click.Context, name: str) -> Any:
        config = _get_config(ctx.parent)
        self.import_xcmd(config)
        return self.commands.get(name)


@click.group(cls=_RootGroup)
@click.version_option(__version__, message="%(version)s")
@click.option(
    "-D",
    "--project-dir",
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=".",
    help="Path to project directory. Default: current.",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="Logging level. Default: 'info'.",
)
@click.option(
    "--color/--no-color",
    default=True,
    help="If set, color console outputs. Default: set",
)
@click.option(
    "--exc-style",
    type=click.Choice(["plain", "pretty"]),
    default="pretty",
    help="Exception style. Default: 'pretty'.",
)
@click.pass_context
def root(
    ctx: click.Context,
    project_dir: Path,
    log_level: str,
    color: bool,
    exc_style: _ExcStyle,
) -> None:
    """A minimal and extensible static website generator"""

    if exc_style == "pretty":
        install(show_locals=True, width=95)
    _set_exc_style(exc_style)

    _set_use_color(color)

    init_logging(log_level)
    ctx.params["log_level"] = log_level
    if log_level == "debug":
        bind_contextvars(subcommand=ctx.invoked_subcommand)
        log.debug(
            "starting Volt",
            version=__version__,
            python_version=sys.version,
            platform=platform(),
        )

    log.debug("setting project dir", path=project_dir)
    ctx.params["project_dir"] = project_dir

    log.debug("setting invocation dir", path=project_dir)
    invoc_dir = Path.cwd()
    ctx.params["invoc_dir"] = invoc_dir

    config: Optional[Config] = None
    if ctx.invoked_subcommand != new.name:

        log.debug("loading config", invoc_dir=invoc_dir, project_dir=project_dir)
        config = Config.from_within_project_dir(invoc_dir, project_dir)
        if config is not None:
            log.debug("loaded config")
        else:
            log.debug("no config found")

    ctx.params["config"] = config

    log.debug("running subcommand")


@root.command()
@click.argument("dir_name", type=str, required=False, default=None)
@click.option(
    "-n",
    "--name",
    type=str,
    required=False,
    default="",
    help=(
        "Name of the static site. If given, the value will be set in the created"
        " config file. Default: empty string or the base name of the project"
        " path, when specified."
    ),
)
@click.option(
    "-u",
    "--url",
    type=str,
    required=False,
    default="",
    help=(
        "URL of the site. If given, the value will be set in the created config file."
        " Default: empty string."
    ),
)
@click.option(
    "-a",
    "--author",
    "authors",
    multiple=True,
    required=False,
    help=(
        "Site author(s). If given, the value will be set in the created config file."
        " Multiple values may be specified. Default: inferred from git config, if"
        " available."
    ),
)
@click.option(
    "-d",
    "--desc",
    type=str,
    default="",
    help=(
        "Site description. If given, the value will be set in the created config file."
        " Default: empty string."
    ),
)
@click.option(
    "--lang",
    type=str,
    default=None,
    help=(
        "Site language. If given, the value will be set in the created config file."
        " Default: inferred from system locale."
    ),
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help=(
        "If set, volt may overwrite files and/or directories in the project directory."
        " Otherwise, the command will fail if any files and/or directories exist in"
        " the target directory."
    ),
)
@click.option(
    "--theme/--no-theme",
    default=True,
    help=(
        "If set, include the default 'ion' theme in the newly created project."
        " Default: set."
    ),
)
@click.option(
    "--vcs",
    type=click.Choice(["none", "git"]),
    default="git",
    help=(
        "The version control system (VCS) initialized in the newly created project."
        " If 'git' is chosen, the created files are also added to the staging area."
        " If 'none' is chosen, no VCS initialization is performed. Default: git."
    ),
)
@click.pass_context
def new(
    ctx: click.Context,
    dir_name: Optional[str],
    name: str,
    url: str,
    authors: tuple[str],
    desc: str,
    lang: Optional[str],
    force: bool,
    theme: bool,
    vcs: _VCS | Literal["none"],
) -> None:
    """Start a new project

    This command creates a new project at the given directory, optionally setting some
    configuration values.

    If DIR_NAME is not specified, this command defaults to creating the project in the
    current directory.

    """
    params = cast(click.Context, ctx.parent).params
    project_dir = session.new(
        dir_name=dir_name,
        invoc_dir=params["invoc_dir"],
        project_dir=params["project_dir"],
        name=name,
        url=url,
        authors=list(authors),
        description=desc,
        language=lang,
        force=force,
        theme="ion" if theme else None,
        vcs=vcs if vcs != "none" else None,
    )
    log.info("project created", path=project_dir)


@root.command()
@click.option(
    "--drafts/--no-drafts",
    default=False,
    help="If set, include the drafts directory as a content source. Default: unset.",
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help=(
        "If set, the target site directory will be removed prior to site"
        " building. Default: set."
    ),
)
@click.pass_context
def build(
    ctx: click.Context,
    drafts: bool,
    clean: bool,
) -> None:
    """Build the site

    This command generates the static site in the site destination directory
    (default: `dist`).

    If no project directory is specified, this command will start lookup of the
    project directory from the current directory upwards. If a project
    directory is specified, no repeated lookups will be performed.

    """
    config = _get_config(ctx.parent, drafts=drafts)

    session.build(config=config, clean=clean)


@root.command()
@click.argument("name", type=str, required=True)
@click.option(
    "-c",
    "--create",
    type=str,
    default=None,
    help=(
        "If set, create a new file in the given section's drafts directory"
        " instead of attempting to edit an existing file. Default: unset."
    ),
)
@click.option(
    "-t",
    "--title",
    type=str,
    default=None,
    help=(
        "The title attribute of the content file, if a new file is created."
        " If '--create' is unset, this flag is ignored."
    ),
)
@click.option(
    "--drafts/--no-drafts",
    default=True,
    help="If set, also look for matches in drafts directories.",
)
@click.pass_context
def edit(
    ctx: click.Context,
    name: str,
    create: Optional[str],
    title: str,
    drafts: bool,
) -> None:
    """Open a source file in an editor"""
    config = _get_config(ctx.parent, drafts=drafts)

    session.edit(config, name, create, title)


@root.group(invoke_without_command=True)
@click.option(
    "-h",
    "--host",
    type=str,
    default=None,
    help="Server host.",
)
@click.option("-p", "--port", type=int, default=5050, help="Server port.")
@click.option(
    "--rebuild/--no-rebuild",
    default=True,
    help="If set, rebuild site when source files are changed. Default: set.",
)
@click.option(
    "--pre-build/--no-pre-build",
    default=True,
    help=(
        "If set, build site before starting server. This value is ignored"
        " if '--build' is unset. Default: set."
    ),
)
@click.option(
    "--drafts/--no-drafts",
    default=True,
    help=(
        "If set, include the drafts directory as a content source when building."
        " Default: set."
    ),
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help=(
        "If set, the target site directory will be removed prior to site"
        " building. Default: set."
    ),
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="If set, hide the startup banner. Default: unset.",
)
@click.option(
    "--sig-handlers/--no-sig-handlers",
    default=True,
    hidden=True,
    help="If set, add custom SIGINT and SIGTERM handlers. Default: set.",
)
@click.pass_context
def serve(
    ctx: click.Context,
    host: Optional[str],
    port: int,
    rebuild: bool,
    pre_build: bool,
    drafts: bool,
    clean: bool,
    quiet: bool,
    sig_handlers: bool,
) -> None:
    """Run the development server"""
    if ctx.invoked_subcommand is not None:
        return None

    if not quiet:
        print(
            """ _    __        __ __
| |  / /____   / // /_
| | / // __ \ / // __/
| |/ // /_/ // // /_
|___/ \____//_/ \__/
""",  # noqa
            file=sys.stderr,
        )

    config = _get_config(ctx.parent, drafts=drafts)
    log_level = cast(str, cast(click.Context, ctx.parent).params["log_level"])

    session.serve(
        config=config,
        host=host,
        port=port,
        rebuild=rebuild,
        pre_build=pre_build,
        build_clean=clean,
        log_level=log_level,
        with_sig_handlers=sig_handlers,
    )


@serve.command("drafts")
@click.option("-s", "--set", "str_value", flag_value="on", help="Turn on drafts mode.")
@click.option(
    "-u", "--unset", "str_value", flag_value="off", help="Turn off drafts mode."
)
@click.option(
    "-t",
    "--toggle",
    "str_value",
    flag_value="unspecified",
    default=True,
    hidden=True,
    help="Toggle currently-set drafts mode.",
)
@click.pass_context
def serve_drafts(
    ctx: click.Context,
    str_value: Literal["on", "off", "unspecified"],
) -> None:
    """Set or unset drafts mode for a running server.

    If neither '-s' or '-u' is specified, this command attempts to toggle the
    currently-set mode, defaulting to '-s' if it fails to do so.

    """
    value: Optional[bool] = None
    if str_value == "on":
        value = True
    elif str_value == "off":
        value = False

    config = _get_config(cast(click.Context, ctx.parent).parent)
    session.serve_drafts(config=config, value=value)

    return None


@root.command(cls=_ExtensionGroup)
def xcmd() -> None:
    """Execute custom subcommands

    Custom subcommands are Click-decorated functions
    defined in the `cli.py` file in your project extension directory.

    """


def _get_config(ctx: Optional[click.Context], drafts: Optional[bool] = None) -> Config:
    if ctx is None:
        raise ValueError("missing expected context")

    config = cast(Optional[Config], ctx.params.get("config"))
    if config is None:
        raise VoltCliError(
            f"command {ctx.invoked_subcommand!r} works only within a Volt project"
        )
    config._set_drafts(drafts)
    return config
