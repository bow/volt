"""Configuration handling."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
from collections import UserDict
from functools import cached_property
from pathlib import Path
from typing import cast, Any, Dict, Iterable, Literal, Optional

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from . import constants, error as err


__all__ = ["Config"]


class Config(UserDict):

    """Container for site-level configuration values."""

    @classmethod
    def from_project_dir(
        cls,
        invoc_dir: Path,
        start_lookup_dir: Path,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> Optional["Config"]:
        """Create an instance from within a project directory.

        This methods performs an upwards traversal from within the current
        directory to look for a YAML config file and loads it.

        :param invoc_dir: Path to invocation directory.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        """
        project_dir = _find_dir_containing(yaml_fname, start_lookup_dir)
        if project_dir is None:
            return None

        return cls.from_yaml(
            invoc_dir=invoc_dir,
            project_dir=project_dir.resolve(),
            yaml_fname=yaml_fname,
            **kwargs,
        )

    @classmethod
    def from_yaml(
        cls,
        invoc_dir: Path,
        project_dir: Path,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> "Config":
        """Create a site configuration from a Volt YAML file.

        :param invoc_dir: Path to the invocation directory.
        :param project_dir: Path to the project working directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        :returns: A site config instance.

        :raises ~exc.VoltConfigError: when validation fails.

        """
        yaml_path = project_dir / yaml_fname
        with yaml_path.open() as src:
            try:
                user_conf = cast(Dict[str, Any], yaml.safe_load(src))
            except (ParserError, ScannerError) as e:
                # TODO: display traceback depending on log level
                raise err.VoltConfigError(f"could not parse config: {e.args[0]}") from e

        return cls(
            invoc_dir=invoc_dir,
            project_dir=project_dir,
            user_conf=user_conf,
            yaml_path=yaml_path,
            **kwargs,
        )

    def __init__(
        self,
        invoc_dir: Path,
        project_dir: Path,
        target_dirname: str = constants.PROJECT_TARGET_DIRNAME,
        sources_dirname: str = constants.PROJECT_SOURCES_DIRNAME,
        themes_dirname: str = constants.SITE_THEMES_DIRNAME,
        static_dirname: str = constants.PROJECT_STATIC_DIRNAME,
        drafts_dirname: str = constants.PROJECT_DRAFTS_DIRNAME,
        extension_dirname: str = constants.PROJECT_EXTENSION_DIRNAME,
        xcmd_fname: str = constants.XCMD_FNAME,
        xcmd_mod_name: str = constants.PROJECT_CLI_MOD_QUALNAME,
        hooks_fname: str = constants.HOOKS_FNAME,
        hooks_mod_name: str = constants.PROJECT_HOOKS_MOD_QUALNAME,
        yaml_path: Optional[Path] = None,
        user_conf: Optional[dict] = None,
        slug_replacements: Iterable[Iterable[str]] = constants.SLUG_REPLACEMENTS,
        **kwargs: Any,
    ) -> None:
        """Initialize a site-level configuration.

        :param invoc_dir: Path to the invocation directory.
        :param project_dir: Path to the project directory.
        :param src_dirname: Base directory name for site source.
        :param out_dirname: Base directory name for site output.

        """
        uc = user_conf or {}
        self._with_drafts: bool = uc.pop("with_drafts", False)
        self._name: str = uc.pop("name", "")
        self._url: str = uc.pop("url", "")
        self._slug_replacements: Iterable[Iterable[str]] = (
            uc.pop("slug_replacements", None) or slug_replacements
        )

        theme_config = uc.pop("theme", {}) or {}
        self._theme_name = theme_config.pop("name", None) or None
        self._theme_overrides = theme_config

        super().__init__(user_conf, **kwargs)

        self._invoc_dir = invoc_dir
        self._project_dir = project_dir
        self._target_dir = project_dir / target_dirname
        self._sources_dir = self._project_dir / sources_dirname
        self._themes_dir = self._project_dir / themes_dirname
        self._extension_dir = self._project_dir / extension_dirname
        self._drafts_dirname = drafts_dirname
        self._static_dir = self._project_dir / static_dirname
        self._xcmd_module_path = self._extension_dir / xcmd_fname
        self._xcmd_module_name = xcmd_mod_name
        self._hooks_module_path = self._extension_dir / hooks_fname
        self._hooks_module_name = hooks_mod_name
        self._yaml_path = yaml_path

    @cached_property
    def name(self) -> str:
        """Name of the site."""
        return self._name

    @cached_property
    def url(self) -> str:
        """URL of the site."""
        return self._url

    @cached_property
    def theme_name(self) -> Optional[str]:
        """Name of theme in use."""
        return self._theme_name

    @cached_property
    def theme_overrides(self) -> dict:
        """Site-level theme overrides."""
        return self._theme_overrides

    @cached_property
    def slug_replacements(self) -> Iterable[Iterable[str]]:
        """Slug replacements rules."""
        return self._slug_replacements

    @cached_property
    def project_dir(self) -> Path:
        """Path to the project root directory."""
        return self._project_dir

    @cached_property
    def project_dir_rel(self) -> Path:
        """Path to the project directory, relative from invocation directory."""
        rel = self.invoc_dir.relative_to(self.project_dir)
        return Path("/".join(("..",) * len(rel.parts)))

    @cached_property
    def invoc_dir(self) -> Path:
        """Path to the invocation directory."""
        return self._invoc_dir

    @cached_property
    def target_dir(self) -> Path:
        """Path to the site output directory."""
        return self._target_dir

    @cached_property
    def sources_dir(self) -> Path:
        """Path to the site source contents."""
        return self._sources_dir

    @cached_property
    def themes_dir(self) -> Path:
        """Path to the site themes directory."""
        return self._themes_dir

    @cached_property
    def drafts_dirname(self) -> str:
        """Name of the drafts directory."""
        return self._drafts_dirname

    @cached_property
    def static_dir(self) -> Path:
        """Path to the site source static files."""
        return self._static_dir

    @cached_property
    def num_common_parts(self) -> int:
        return len(self.project_dir.parts) + 1

    @cached_property
    def xcmd_module_path(self) -> Optional[Path]:
        """Path to a custom CLI extension, if present."""
        fp = self._xcmd_module_path
        if fp.exists():
            return fp
        return None

    @cached_property
    def xcmd_module_name(self) -> str:
        """Module name for CLI extensions."""
        return self._xcmd_module_name

    @cached_property
    def hooks_module_path(self) -> Optional[Path]:
        """Path to a custom hooks extension, if present."""
        fp = self._hooks_module_path
        if fp.exists():
            return fp
        return None

    @cached_property
    def hooks_module_name(self) -> str:
        """Module name for hooks."""
        return self._hooks_module_name

    @cached_property
    def with_drafts(self) -> bool:
        """Whether to publish draft contents or not."""
        return self._with_drafts

    @cached_property
    def in_docker(self) -> bool:
        return os.path.exists("/.dockerenv")

    def reload(self) -> "Config":
        """Reloads a YAML config."""
        if self._yaml_path is None:
            raise err.VoltResourceError("could not reload non-YAML config")
        return self.__class__.from_yaml(
            invoc_dir=self.invoc_dir, project_dir=self.project_dir
        )


_VCS = Literal["git"]
_ExcStyle = Literal["pretty", "plain"]

# NOTE: Not context vars because our watchers and server are thread-based
#       without any clean ways of propagating the contexts.
_use_color: bool = True
_exc_style: _ExcStyle = "pretty"


def _get_use_color() -> bool:
    global _use_color
    return _use_color


def _set_use_color(value: bool) -> bool:
    global _use_color
    cur = _use_color
    _use_color = value
    return cur


def _get_exc_style() -> _ExcStyle:
    global _exc_style
    return _exc_style


def _set_exc_style(value: _ExcStyle) -> _ExcStyle:
    global _exc_style
    cur = _exc_style
    _exc_style = value
    return cur


def _find_dir_containing(fname: str, start: Path) -> Optional[Path]:
    """Find the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param fname: The filename that should be present in the directory.
    :param start: The path from which lookup starts.

    :returns: The path to the directory that contains the filename or None if
        no such path can be found.

    """
    cur = Path(start).expanduser().resolve()

    while cur != cur.parent:
        if cur.joinpath(fname).exists():
            return cur
        cur = cur.parent

    return None
