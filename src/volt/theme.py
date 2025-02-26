"""Site theme."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from collections.abc import Callable
from copy import deepcopy
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Optional, Self, cast

import jinja2.exceptions as j2exc
import tomlkit
from jinja2 import Environment, FileSystemLoader, Template

from . import constants
from . import error as err
from ._import import import_file
from ._logging import log_method
from .config import Config

if TYPE_CHECKING:
    from .engines import EngineSpec


__all__ = ["Theme"]


class Theme:
    """Site theme."""

    @classmethod
    @log_method
    def from_config(cls, config: Config) -> Self:
        if config.theme_source is None:
            raise err.VoltConfigError("config defines no theme")

        name = config.theme_source.get("local", None) or None
        if name is None:
            raise err.VoltConfigError(
                "config.theme.source is missing required 'local' key"
            )

        path = config.themes_dir / name
        if not path.exists():
            raise err.VoltConfigError(f"local theme {name!r} not found")

        if not (path / constants.THEME_MANIFEST_FILE_NAME).exists():
            raise err.VoltConfigError(
                f"manifest file {constants.THEME_MANIFEST_FILE_NAME!r}"
                f" not found for local theme {name!r}"
            )

        return cls(path=path, site_config=config)

    def __init__(self, path: Path, site_config: Config) -> None:
        self._path = path
        self._config = site_config
        self._opts = self._resolve_opts()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, ...)"

    @property
    def opts(self) -> dict:
        """Theme options."""
        return self._opts

    @property
    def hooks(self) -> dict:
        """Theme hooks."""
        return self.opts.get("hooks", {}) or {}

    def get_hook_config(self, name: str) -> dict:
        """Retrieve config for the given hook."""
        return self.hooks.get(name) or {}

    def hook_enabled(self, name: str) -> bool:
        """Check whether the given hook is enabled."""
        return self.get_hook_config(name).get("enabled") or False

    @cached_property
    def path(self) -> Path:
        """Path to the theme directory."""
        return self._path

    @cached_property
    def name(self) -> Optional[str]:
        """Theme name."""
        return self.manifest.get("name")

    @cached_property
    def description(self) -> Optional[str]:
        """Theme description."""
        return self.manifest.get("description")

    @cached_property
    def authors(self) -> list[str]:
        """Theme authors."""
        return cast(list[str], self.manifest.get("authors", []))

    @cached_property
    def module_name(self) -> str:
        """Module name of the theme."""
        return f"{constants.THEME_ROOT_MOD_QUAL_NAME}.{self.path.name}"

    @cached_property
    def engine_module_name(self) -> str:
        """Module name for theme engines."""
        return f"{self.module_name}.{constants.ENGINES_MOD_NAME}"

    @cached_property
    def engine_module_path(self) -> Path:
        """Path to theme engines."""
        return self.path / constants.ENGINE_FILE_NAME

    @cached_property
    def hooks_module_name(self) -> str:
        """Module name for theme hooks."""
        return f"{self.module_name}.{constants.HOOKS_MOD_NAME}"

    @cached_property
    def hooks_module_path(self) -> Path:
        """Path to the theme hooks file."""
        return self.path / constants.HOOKS_FILE_NAME

    @cached_property
    def template_extension_module_name(self) -> str:
        """Module name for theme template extensions."""
        return f"{self.module_name}.{constants.TEMPLATE_FUNCTIONS_MOD_NAME}"

    @cached_property
    def template_extension_module_path(self) -> Path:
        """Path to theme template extensions."""
        return self.path / constants.TEMPLATE_FUNCTIONS_FILE_NAME

    @cached_property
    def static_dir(self) -> Path:
        """Path to the site static files."""
        return self.path / constants.THEME_STATIC_DIR_NAME

    @property
    def config(self) -> Config:
        """Site-level configurations."""
        return self._config

    @cached_property
    def manifest_path(self) -> Path:
        """Path to theme manifest."""
        return self.path / constants.THEME_MANIFEST_FILE_NAME

    @cached_property
    def manifest(self) -> dict:
        """Theme manifest contents."""
        with self.manifest_path.open("r") as src:
            manifest = tomlkit.load(src).get("theme", {})
        return cast(dict, manifest)

    @cached_property
    def defaults(self) -> dict:
        """Theme defaults."""
        return self.manifest.get("defaults", {}) or {}

    @cached_property
    def templates_dir(self) -> Path:
        """Path to the theme template directory."""
        return self.path / constants.THEME_TEMPLATES_DIR_NAME

    @cached_property
    def template_env(self) -> Environment:
        """Theme template environment."""
        env = Environment(  # nosec
            loader=FileSystemLoader(self.templates_dir),
            auto_reload=True,
            enable_async=True,
        )
        self._set_template_extensions(env)

        return env

    @log_method
    def _set_template_extensions(self, env: Environment) -> None:
        if (mod := self._load_template_extension()) is None:
            return None

        def get(kind: str, mark: str, container: dict[str, Any]) -> None:
            funcs: dict[str, Callable] = {
                obj._volt_template_filter: obj
                for obj in mod.__dict__.values()
                if callable(obj) and hasattr(obj, mark)
            }

            for ext_name, ext_func in funcs.items():
                if ext_name in container:
                    raise err.VoltError(f"{kind} function {ext_name!r} already defined")
                container[ext_name] = ext_func

        get("filter", constants.TEMPLATE_FILTER_MARK, env.filters)
        get("test", constants.TEMPLATE_TEST_MARK, env.tests)

        return None

    @log_method(with_args=True)
    def _load_template_extension(self) -> Optional[ModuleType]:
        """Load custom template extension functions."""
        try:
            return import_file(
                self.template_extension_module_path,
                self.template_extension_module_name,
            )
        except FileNotFoundError:
            return None

    @log_method
    def get_engine_spec(self) -> Optional["EngineSpec"]:
        from .engines import EngineSpec

        engine_config = self.manifest.get("engine", None) or None
        if not engine_config:
            return None

        mod = engine_config.get("module", None)
        cls = engine_config.get("class", None)

        # If no engines are specified, assume that we are using
        # the default MarkdownEngine.
        if mod is None and cls is None:
            mod = "volt.engines:MarkdownEngine"

        return EngineSpec(
            config=self.config,
            theme=self,
            module=mod,
            klass=cls,
        )

    @log_method(with_args=True)
    def _resolve_opts(self) -> dict:
        return _overlay(self.defaults, self.config.theme_overrides.get("overrides"))

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


def _overlay(base: Optional[dict], mod: Optional[dict]) -> dict:
    _nonexistent = object()

    def func(overlaid: dict, mod: dict) -> None:
        for mk, mv in mod.items():
            ov = overlaid.get(mk, _nonexistent)
            if (
                ov is _nonexistent
                or not isinstance(mv, dict)
                or not isinstance(ov, dict)
            ):
                overlaid[mk] = mv
            else:
                func(ov, mv)

    overlaid = deepcopy(base) if base is not None else {}
    func(overlaid, mod or {})

    return overlaid
