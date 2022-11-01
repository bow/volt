"""Site theme."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import yaml
from pathlib import Path
from functools import cached_property
from typing import cast, Optional, TYPE_CHECKING

import jinja2.exceptions as j2exc
from jinja2 import Environment, FileSystemLoader, Template

from . import constants, error as err
from .config import Config
from .targets import collect_copy_targets, CopyTarget
from ._logging import log_method

if TYPE_CHECKING:
    from .engines import Engine


__all__ = ["Theme"]


class Theme:

    """Site theme."""

    @classmethod
    @log_method
    def from_config(cls, config: Config) -> "Theme":

        if (theme_config := config.theme) is None:
            raise err.VoltConfigError("undefined theme")

        if (theme_name := theme_config.get("name", None)) is None:
            raise err.VoltConfigError("missing theme name")

        theme_opts = theme_config.get("opts", None) or {}

        return cls(name=theme_name, opts=theme_opts, config=config)

    def __init__(self, name: str, opts: dict, config: Config) -> None:
        self.name = name
        self.opts = opts
        self.config = config

        theme_dir = config.themes_dir / self.name
        if not theme_dir.exists():
            raise err.VoltConfigError(
                f"theme {self.name!r} not found in {config.themes_dir}"
            )

        self.path = theme_dir

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, ...)"

    @cached_property
    def static_dir(self) -> Path:
        """Path to the site source theme static files."""
        return self.path / constants.THEME_STATIC_DIRNAME

    @cached_property
    def engines_dir(self) -> Path:
        """Path to the theme engines directory."""
        return self.path / constants.SITE_THEME_ENGINES_DIRNAME

    @cached_property
    def config_dir(self) -> Path:
        """Path to theme default configurations."""
        return self.path / constants.THEME_SETTINGS_FNAME

    @cached_property
    def defaults(self) -> dict:
        """Default theme configurations."""
        with self.config_dir.open("r") as src:
            return cast(dict, yaml.safe_load(src))

    @cached_property
    def templates_dir(self) -> Path:
        """Path to the theme template directory."""
        return self.path / constants.SITE_THEME_TEMPLATES_DIRNAME

    @cached_property
    def template_env(self) -> Environment:
        """Theme template environment."""
        return Environment(  # nosec
            loader=FileSystemLoader(self.templates_dir),
            auto_reload=True,
            enable_async=True,
        )

    @log_method
    def collect_static_targets(self) -> list[CopyTarget]:
        return collect_copy_targets(self.static_dir, self.config.invoc_dir)

    @log_method
    def load_engines(self) -> Optional[list["Engine"]]:

        from .engines import EngineSpec

        config = self.config
        engine_configs: Optional[list[dict]] = self.opts.get(
            "engines", self.defaults.get("engines", None)
        )

        if engine_configs is None:
            return None

        engines = [
            spec.load()
            for spec in (
                EngineSpec(
                    config=config,
                    theme=self,
                    source=entry.get("source", ""),
                    opts=entry.get("opts", {}),
                    module=entry.get("module", None),
                    file=entry.get("file", None),
                )
                for entry in engine_configs
            )
        ]

        return engines

    @log_method(with_args=True)
    def load_template_file(self, name: str) -> Template:
        """Load a template with the given file name."""
        try:
            template = self.template_env.get_template(name)
        except j2exc.TemplateNotFound as e:
            raise err.VoltMissingTemplateError(
                f"could not find template {name!r}"
            ) from e
        except j2exc.TemplateSyntaxError as e:
            raise err.VoltResourceError(
                f"template {name!r} has syntax errors: {e.message}"
            ) from e

        return template

    @log_method(with_args=True)
    def load_template(self, key: str) -> Template:
        """Load a theme template with the given key."""

        theme_templates = self.defaults["templates"]

        try:
            template_name = theme_templates[key]
        except KeyError as e:
            raise err.VoltResourceError(
                f"could not find template {key!r} in theme settings"
            ) from e

        template = self.load_template_file(template_name)

        return template
