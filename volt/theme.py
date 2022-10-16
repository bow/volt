"""Site theme."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import yaml
from pathlib import Path
from functools import cached_property
from typing import cast, Optional, TYPE_CHECKING

import jinja2.exceptions as j2exc
from jinja2 import Environment, FileSystemLoader, Template

from . import constants, exceptions as excs
from .config import SiteConfig
from .targets import collect_copy_targets, CopyTarget

if TYPE_CHECKING:
    from .engines import Engine


class Theme:

    """Site theme."""

    @classmethod
    def from_site_config(cls, site_config: SiteConfig) -> "Theme":

        if (theme_config := site_config.theme) is None:
            raise excs.VoltConfigError("undefined theme")

        if (theme_name := theme_config.get("name", None)) is None:
            raise excs.VoltConfigError("missing theme name")

        theme_opts = theme_config.get("opts", None) or {}

        return cls(name=theme_name, opts=theme_opts, site_config=site_config)

    def __init__(self, name: str, opts: dict, site_config: SiteConfig) -> None:
        self.name = name
        self.opts = opts
        self.site_config = site_config

        theme_path = site_config.themes_path / self.name
        if not theme_path.exists():
            raise excs.VoltConfigError(
                f"theme {self.name!r} not found in {site_config.themes_path}"
            )

        self.path = theme_path

    @cached_property
    def static_path(self) -> Path:
        """Path to the site source theme static files."""
        return self.path / constants.SITE_STATIC_DIRNAME

    @cached_property
    def engines_path(self) -> Path:
        """Path to the theme engines directory."""
        return self.path / constants.SITE_THEME_ENGINES_DIRNAME

    @cached_property
    def config_path(self) -> Path:
        """Path to theme default configurations."""
        return self.path / constants.THEME_SETTINGS_FNAME

    @cached_property
    def defaults(self) -> dict:
        """Default theme configurations."""
        with self.config_path.open("r") as src:
            return cast(dict, yaml.safe_load(src))

    @cached_property
    def template_path(self) -> Path:
        """Path to the theme template directory."""
        return self.path / constants.SITE_THEME_TEMPLATES_DIRNAME

    @cached_property
    def template_env(self) -> Environment:
        """Theme template environment."""
        return Environment(  # nosec
            loader=FileSystemLoader(self.template_path),
            auto_reload=True,
            enable_async=True,
        )

    def collect_static_targets(self) -> list[CopyTarget]:
        return collect_copy_targets(self.static_path, self.site_config.cwd)

    def load_engines(self) -> Optional[list["Engine"]]:

        from .engines import EngineSpec

        site_config = self.site_config
        engine_configs: Optional[list[dict]] = self.opts.get(
            "engines", self.defaults.get("engines", None)
        )

        if engine_configs is None:
            return None

        engines = [
            spec.load()
            for spec in (
                EngineSpec(
                    site_config=site_config,
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

    def load_template_file(self, name: str) -> Template:
        """Load a template with the given file name."""
        try:
            template = self.template_env.get_template(name)
        except j2exc.TemplateNotFound as e:
            raise excs.VoltMissingTemplateError(
                f"could not find template {name!r}"
            ) from e
        except j2exc.TemplateSyntaxError as e:
            raise excs.VoltResourceError(
                f"template {name!r} has syntax errors: {e.message}"
            ) from e

        return template

    def load_template(self, key: str) -> Template:
        """Load a theme template with the given key."""

        theme_templates = self.defaults["templates"]

        try:
            template_name = theme_templates[key]
        except KeyError as e:
            raise excs.VoltResourceError(
                f"could not find template {key!r} in theme settings"
            ) from e

        template = self.load_template_file(template_name)

        return template
