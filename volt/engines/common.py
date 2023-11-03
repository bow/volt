"""Common engine functions and classes."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import abc
from dataclasses import dataclass, field, InitVar
from importlib import import_module
from pathlib import Path
from typing import cast, Any, Optional, Sequence, Type

import structlog

from .. import error as err
from ..config import Config
from ..outputs import Output
from ..theme import Theme
from .._import import import_file
from .._logging import log_method


log = structlog.get_logger(__name__)


class Engine(abc.ABC):

    """Object for creating site outputs."""

    def __init__(
        self,
        config: Config,
        theme: Theme,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.config = config
        self.theme = theme

    @property
    def name(self) -> str:
        """Name of the engine class."""
        return self.__class__.__name__

    @property
    def contents_dir(self) -> Path:
        """Path to the root contents directory for this engine."""
        return self.config.contents_dir

    @abc.abstractmethod
    def prepare_outputs(
        self,
        with_draft: bool,
        *args: Any,
        **kwargs: Any,
    ) -> Sequence[Output]:
        raise NotImplementedError()


@dataclass(eq=True, repr=True)
class EngineSpec:

    """Specifications of an engine in the config."""

    config: Config
    theme: Theme
    engine: Type[Engine] = field(init=False)
    module: InitVar[Optional[str]]
    klass: InitVar[Optional[str]]

    def __post_init__(
        self,
        module: Optional[str],
        klass: Optional[str],
    ) -> None:
        match (module, klass):
            case (m, None) if isinstance(m, str):
                self.engine = self._load_engine_module(m)

            case (None, f) if isinstance(f, str):
                # TODO: Expand to also be able to load packages, not just modules.
                self.engine = self._load_engine_class(self.theme, f)

            case (None, None):
                msg = "one of 'module' or 'class' must be a valid string value"
                raise err.VoltConfigError(msg)

            case (_, _):
                msg = "only one of 'module' or 'class' may be specified"
                raise err.VoltConfigError(msg)

    @log_method
    def load(self) -> Engine:
        return self.engine(config=self.config, theme=self.theme)

    @log_method(with_args=True)
    def _load_engine_module(self, mod_spec: str) -> Type[Engine]:
        mod_name, cls_name = self._parse_class_spec(mod_spec)

        try:
            mod = import_module(mod_name)
        except ModuleNotFoundError as e:
            raise err.VoltConfigError(f"not a valid module: {mod_name}") from e

        try:
            return cast(Type[Engine], getattr(mod, cls_name))
        except AttributeError as e:
            raise err.VoltConfigError(
                f"engine {cls_name!r} not found in module {mod_name!r}"
            ) from e

    @log_method(with_args=True)
    def _load_engine_class(
        self,
        theme: Theme,
        name: str,
    ) -> Type[Engine]:
        if not name.isidentifier():
            raise err.VoltConfigError(f"invalid engine class specifier: {name!r}")

        fp = theme.engine_module_path
        if not fp.exists():
            raise err.VoltConfigError("theme engine file not found")

        mod_name = theme.engine_module_name

        log.debug("loading file as module", path=fp, module=mod_name)
        mod = import_file(fp, mod_name)

        try:
            return cast(Type[Engine], getattr(mod, name))
        except AttributeError as e:
            raise err.VoltConfigError(
                f"engine {name!r} not found in file {str(fp)!r}"
            ) from e

    @staticmethod
    def _parse_class_spec(spec: str) -> tuple[str, str]:
        try:
            cls_loc, cls_name = spec.rsplit(":", 1)
        except ValueError:
            raise err.VoltConfigError(f"invalid engine class specifier: {spec!r}")
        return cls_loc, cls_name
