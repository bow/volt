"""Configuration handling."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
from collections import UserDict
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Optional, Self, cast

import tomlkit

from . import constants
from . import error as err

__all__ = ["Config"]


class Config(UserDict):
    """Container for site-level configuration values."""

    @classmethod
    def from_within_project_dir(
        cls,
        invoc_dir: Path,
        start_lookup_dir: Path,
        config_file_name: str = constants.CONFIG_FILE_NAME,
        **kwargs: Any,
    ) -> Optional[Self]:
        """Create an instance from within a project directory.

        This methods performs an upwards traversal from within the current
        directory to look for a config file and loads it.

        :param invoc_dir: Path to invocation directory.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param config_file_name: Name of file containing the configuration values.

        """
        project_dir = _find_dir_containing(config_file_name, start_lookup_dir)
        if project_dir is None:
            return None

        return cls.from_file_name(
            invoc_dir=invoc_dir,
            project_dir=project_dir.resolve(),
            config_file_name=config_file_name,
            **kwargs,
        )

    @classmethod
    def from_file_name(
        cls,
        invoc_dir: Path,
        project_dir: Path,
        config_file_name: str,
        **kwargs: Any,
    ) -> Self:
        """Create a site configuration from a volt config file.

        :param invoc_dir: Path to the invocation directory.
        :param project_dir: Path to the project working directory.
        :param config_file_name: Name of file containing the configuration values.

        :returns: A site config instance.

        :raises ~exc.VoltConfigError: when validation fails.

        """
        config_path = project_dir / config_file_name
        with config_path.open() as src:
            user_conf = cast(Dict[str, Any], tomlkit.load(src))

        return cls(
            invoc_dir=invoc_dir,
            project_dir=project_dir,
            user_conf=user_conf,
            config_path=config_path,
            **kwargs,
        )

    def __init__(
        self,
        invoc_dir: Path,
        project_dir: Path,
        output_dir_name: str = constants.PROJECT_OUTPUT_DIR_NAME,
        contents_dir_name: str = constants.PROJECT_CONTENTS_DIR_NAME,
        themes_dir_name: str = constants.SITE_THEMES_DIR_NAME,
        static_dir_name: str = constants.PROJECT_STATIC_DIR_NAME,
        draft_dir_name: str = constants.PROJECT_DRAFT_DIR_NAME,
        extension_dir_name: str = constants.PROJECT_EXTENSION_DIR_NAME,
        xcmd_file_name: str = constants.XCMD_FILE_NAME,
        xcmd_mod_name: str = constants.PROJECT_CLI_MOD_QUAL_NAME,
        hooks_file_name: str = constants.HOOKS_FILE_NAME,
        hooks_mod_name: str = constants.PROJECT_HOOKS_MOD_QUAL_NAME,
        config_path: Optional[Path] = None,
        user_conf: Optional[dict] = None,
        slug_replacements: Iterable[Iterable[str]] = constants.SLUG_REPLACEMENTS,
        **kwargs: Any,
    ) -> None:
        """Initialize a site-level configuration."""
        uc = user_conf or {}

        site_config = uc.pop("site", {})
        self._name: str = site_config.pop("name", "")
        self._url: str = site_config.pop("url", "")
        self._slug_replacements: Iterable[Iterable[str]] = (
            site_config.pop("slug_replacements", None) or slug_replacements
        )

        theme_config = uc.pop("theme", {}) or {}
        self._theme_source = theme_config.pop("source", None) or None
        self._theme_overrides = theme_config

        super().__init__(site_config, **kwargs)

        self._invoc_dir = invoc_dir
        self._project_dir = project_dir
        self._output_dir = project_dir / output_dir_name
        self._contents_dir = self._project_dir / contents_dir_name
        self._themes_dir = self._project_dir / themes_dir_name
        self._extension_dir = self._project_dir / extension_dir_name
        self._draft_dir_name = draft_dir_name
        self._draft_contents_dir = (
            self._project_dir / contents_dir_name / draft_dir_name
        )
        self._draft_static_dir = (
            self._project_dir / contents_dir_name / draft_dir_name / static_dir_name
        )
        self._static_dir = self._project_dir / contents_dir_name / static_dir_name
        self._xcmd_module_path = self._extension_dir / xcmd_file_name
        self._xcmd_module_name = xcmd_mod_name
        self._hooks_module_path = self._extension_dir / hooks_file_name
        self._hooks_module_name = hooks_mod_name
        self._config_path = config_path

        self._server_run_path = project_dir / constants.SERVER_RUN_FILE_NAME

    @property
    def name(self) -> str:
        """Name of the site."""
        return self._name

    @property
    def url(self) -> str:
        """URL of the site."""
        return self._url

    @property
    def theme_source(self) -> Optional[dict]:
        """Source of theme in use."""
        return self._theme_source

    @property
    def theme_overrides(self) -> dict:
        """Site-level theme overrides."""
        return self._theme_overrides

    @property
    def slug_replacements(self) -> Iterable[Iterable[str]]:
        """Slug replacements rules."""
        return self._slug_replacements

    @property
    def project_dir(self) -> Path:
        """Path to the project root directory."""
        return self._project_dir

    @cached_property
    def project_dir_rel(self) -> Path:
        """Path to the project directory, relative from invocation directory."""
        rel = self.invoc_dir.relative_to(self.project_dir)
        return Path("/".join(("..",) * len(rel.parts)))

    @property
    def invoc_dir(self) -> Path:
        """Path to the invocation directory."""
        return self._invoc_dir

    @property
    def output_dir(self) -> Path:
        """Path to the site output directory."""
        return self._output_dir

    @property
    def contents_dir(self) -> Path:
        """Path to the site contents."""
        return self._contents_dir

    @property
    def themes_dir(self) -> Path:
        """Path to the site themes directory."""
        return self._themes_dir

    @property
    def draft_dir_name(self) -> str:
        """Name of the draft directory."""
        return self._draft_dir_name

    @property
    def draft_contents_dir(self) -> Path:
        """Path to the site draft contents files."""
        return self._draft_contents_dir

    @property
    def draft_static_dir(self) -> Path:
        """Path to the site draft static files."""
        return self._draft_static_dir

    @property
    def static_dir(self) -> Path:
        """Path to the site contents static files."""
        return self._static_dir

    @cached_property
    def num_common_parts(self) -> int:
        return len(self.project_dir.parts) + 1

    @property
    def xcmd_module_path(self) -> Path:
        """Path to a custom CLI extension."""
        return self._xcmd_module_path

    @property
    def xcmd_module_name(self) -> str:
        """Module name for CLI extensions."""
        return self._xcmd_module_name

    @property
    def hooks_module_path(self) -> Path:
        """Path to a custom hooks extension."""
        return self._hooks_module_path

    @property
    def hooks_module_name(self) -> str:
        """Module name for hooks."""
        return self._hooks_module_name

    @property
    def in_docker(self) -> bool:
        return os.path.exists("/.dockerenv")

    def reload(self, config_file_name: str = constants.CONFIG_FILE_NAME) -> Self:
        """Reloads the config file."""
        if self._config_path is None:
            raise err.VoltResourceError("could not reload non-file config")
        return self.__class__.from_file_name(
            invoc_dir=self.invoc_dir,
            project_dir=self.project_dir,
            config_file_name=config_file_name,
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


def _find_dir_containing(file_name: str, start: Path) -> Optional[Path]:
    """Find the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param file_name: The file name that should be present in the directory.
    :param start: The path from which lookup starts.

    :returns: The path to the directory that contains the filename or None if
        no such path can be found.

    """
    cur = Path(start).expanduser().resolve()

    while cur != cur.parent:
        if cur.joinpath(file_name).exists():
            return cur
        cur = cur.parent

    return None
