"""Main entry point for command line invocation."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import time
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, cast

import click
import pendulum

from . import __version__, constants
from . import exceptions as excs
from .config import SiteConfig
from .server import Rebuilder, make_server
from .site import Site
from .utils import (
    echo_err,
    echo_info,
    get_fuzzy_match,
    infer_front_matter,
    import_file,
)


class Session:

    """Commands for a single CLI session."""

    @staticmethod
    def do_init(
        cwd: Path,
        pwd: Optional[Path],
        name: Optional[str],
        url: Optional[str],
        force: bool,
        config_fname: str = constants.CONFIG_FNAME,
    ) -> Path:
        """Initialize a new project.

        This function may overwrite any preexisting files and or directories
        in the target working directory.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project directory to be created.
        :param name: Name of the static site, to be put inside the generated
            config file.
        :param url: URL of the static site, to be put inside the generated
            config file.
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
            raise excs.VoltCliError(e.strerror) from e

        if not force and any(True for _ in pwd.iterdir()):
            raise excs.VoltCliError(
                "target project directory is not empty -- use the `-f` flag to"
                " force init in nonempty directories"
            )

        # Bootstrap directories.
        bootstrap_conf = SiteConfig(cwd=cwd, pwd=pwd)
        bootstrap_path_attrs = [
            "sources_path",
            "static_path",
            "theme_path",
        ]
        try:
            for attr in bootstrap_path_attrs:
                getattr(bootstrap_conf, attr).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise excs.VoltCliError(e.strerror) from e

        # Create initial YAML config file.
        init_conf = f"""---
# Volt configuration file.
name: "{name or ''}"
url: "{url or ''}"
description: ""
author: ""
language: ""
"""

        # Create initial YAML config file.
        (pwd / config_fname).write_text(init_conf)

        return pwd

    @staticmethod
    def do_build(
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

    @staticmethod
    def do_edit(
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

    @staticmethod
    def do_serve(
        sc: SiteConfig,
        host: str,
        port: int,
        build: bool,
        build_with_drafts: bool,
        build_clean: bool,
    ) -> None:

        serve = make_server(sc, host, port)

        if build:

            rebuild_count = 0

            def builder() -> None:
                nonlocal sc, rebuild_count
                if rebuild_count > 0:
                    echo_info("detected source change -- rebuilding")
                try:
                    # TODO: Only reload config post-init, on config file change.
                    sc = sc.reload()
                    Session.do_build(sc, build_clean, build_with_drafts)
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


# Taken from:
# https://click.palletsprojects.com/en/8.0.x/advanced/#command-aliases
class AliasedGroup(click.Group):
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


@click.group(cls=AliasedGroup)
@click.version_option(__version__)
@click.option(
    "-D",
    "--project-dir",
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    default=None,
    help="Path to project directory. Default: current.",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="Logging level. Default: 'info'.",
)
@click.pass_context
def main(ctx: click.Context, project_dir: Optional[str], log_level: str) -> None:
    """A versatile static website generator"""
    ctx.params["log_level"] = log_level

    project_path = Path(project_dir) if project_dir is not None else None
    ctx.params["project_path"] = project_path

    sc: Optional[SiteConfig] = None
    if ctx.invoked_subcommand != "init":
        sc = SiteConfig.from_project_yaml(Path.cwd(), project_path)
    ctx.params["site_config"] = sc


@main.command()
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
    ),
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
    ),
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help=(
        "If set, volt may overwrite any files and/or directories in the init"
        " directory. Otherwise, init will fail if any files and/or directories"
        " exist in the target directory."
    ),
)
@click.pass_context
def init(
    ctx: click.Context,
    name: Optional[str],
    url: Optional[str],
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
    params = cast(click.Context, ctx.parent).params
    pwd = Session.do_init(
        Path.cwd(),
        params["project_path"],
        name,
        url,
        force,
    )
    echo_info(f"project initialized at {pwd}")


@main.command()
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
    """Build static site.

    This command generates the static site in the site destination directory
    (default: `dist`).

    If no project directory is specified, this command will start lookup of the
    project directory from the current directory upwards. If a project
    directory is specified, no repeated lookups will be performed.

    """
    params = cast(click.Context, ctx.parent).params
    sc = params.get("site_config", None)
    if sc is None:
        raise excs.VOLT_NO_PROJECT_ERR

    Session.do_build(sc, clean, drafts)


@main.command()
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
    """Open a draft file in an editor."""
    params = cast(click.Context, ctx.parent).params
    sc = params.get("site_config", None)
    if sc is None:
        raise excs.VOLT_NO_PROJECT_ERR

    Session.do_edit(sc, name, create, title, drafts)


@main.command()
@click.option("-h", "--host", type=str, default="127.0.0.1", help="Server host.")
@click.option("-p", "--port", type=int, default=5050, help="Server port.")
@click.option(
    "--build/--no-build",
    default=True,
    help="If set, rebuild site when source files are changed. Default: set.",
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
@click.pass_context
def serve(
    ctx: click.Context,
    host: str,
    port: int,
    build: bool,
    drafts: bool,
    clean: bool,
) -> None:
    """Run the development server."""
    params = cast(click.Context, ctx.parent).params
    sc = params.get("site_config", None)
    if sc is None:
        raise excs.VOLT_NO_PROJECT_ERR

    Session.do_serve(sc, host, port, build, drafts, clean)


class ExtensionGroup(click.Group):
    @classmethod
    def import_xcmd(
        cls,
        sc: SiteConfig,
        mod_name: str = "volt.ext.command",
    ) -> Optional[ModuleType]:
        """Import the custom, user-defined subcommands."""
        if (fp := sc.xcmd_script_path) is None:
            return None

        mod = import_file(fp, mod_name)

        return mod

    def list_commands(self, ctx: click.Context) -> list[str]:
        params = cast(click.Context, ctx.parent).params
        sc = params["site_config"]

        if (mod := self.import_xcmd(sc)) is None:
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
        params = cast(click.Context, ctx.parent).params
        sc = params["site_config"]
        self.import_xcmd(sc)
        return self.commands.get(name)


@main.command(cls=ExtensionGroup)
def xcmd() -> None:
    """Execute custom subcommands.

    Custom subcommands are Click-decorated functions
    defined in an `ext/cmd.py` file in your project.

    """
