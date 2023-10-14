"""Site theme."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import tomlkit
from copy import deepcopy
from pathlib import Path
from functools import cached_property
from types import ModuleType
from typing import cast, Any, Callable, Literal, Optional, Self, TYPE_CHECKING

import jinja2.exceptions as j2exc
from jinja2 import Environment, FileSystemLoader, Template

from . import constants, error as err
from .config import Config
from ._logging import log_method
from ._import import import_file

if TYPE_CHECKING:
    from .engines import EngineSpec


__all__ = ["Theme"]


class Theme:

    """Site theme."""

    @classmethod
    @log_method
    def from_config(cls, config: Config) -> Self:
        if config.theme_name is None:
            raise err.VoltConfigError("config defines no theme")

        return cls(name=config.theme_name, site_config=config)

    def __init__(self, name: str, site_config: Config) -> None:
        self._name = name
        self._config = site_config

        theme_dir = site_config.themes_dir / self.name
        if not theme_dir.exists():
            raise err.VoltConfigError(
                f"theme {self.name!r} not found in {site_config.themes_dir}"
            )
        self._path = theme_dir

        self._opts = self._resolve_config("opts")
        self._engine = self._resolve_config("engine")
        self._hooks = self._resolve_config("hooks")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, ...)"

    @property
    def name(self) -> str:
        """Theme name."""
        return self._name

    @property
    def opts(self) -> dict:
        """Theme options."""
        return self._opts

    @property
    def engine(self) -> dict:
        """Theme engine."""
        return self._engine

    @property
    def hooks(self) -> dict:
        """Theme hooks."""
        return self._hooks

    def get_hook_config(self, name: str) -> dict:
        """Retrieve config for the given hook."""
        return self.hooks.get(name) or {}

    def hook_enabled(self, name: str) -> bool:
        """Check whether the given hook is enabled."""
        return self.get_hook_config(name).get("enabled") or False

    @property
    def path(self) -> Path:
        """Path to the theme directory."""
        return self._path

    @cached_property
    def module_name(self) -> str:
        """Module name of the theme."""
        return f"{constants.THEME_ROOT_MOD_QUAL_NAME}.{self.name}"

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
        return f"{self.module_name}.{constants.TEMPLATE_EXTENSIONS_MOD_NAME}"

    @cached_property
    def template_extension_module_path(self) -> Path:
        """Path to theme template extensions."""
        return self.path / constants.TEMPLATE_EXTENSIONS_FILE_NAME

    @cached_property
    def static_dir(self) -> Path:
        """Path to the site static files."""
        return self.path / constants.THEME_STATIC_DIR_NAME

    @property
    def config(self) -> Config:
        """Site-level configurations."""
        return self._config

    @cached_property
    def config_defaults_path(self) -> Path:
        """Path to theme default configurations."""
        return self.path / constants.THEME_SETTINGS_FILE_NAME

    @cached_property
    def config_defaults(self) -> dict:
        """Default theme configurations."""
        with self.config_defaults_path.open("r") as src:
            return cast(dict, tomlkit.load(src)).get("theme", {})

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

        if not self.engine:
            return None

        return EngineSpec(
            config=self.config,
            theme=self,
            opts=self.engine.get("opts", {}),
            module=self.engine.get("module", None),
            klass=self.engine.get("class", None),
        )

    @log_method(with_args=True)
    def _resolve_config(self, key: Literal["engine", "hooks", "opts"]) -> dict:
        """Resolve theme configuration by applying overrides to defaults"""
        return _overlay(
            self.config_defaults.get(key, None),
            self.config.theme_overrides.get(key, None),
        )

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
