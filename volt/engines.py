"""Site engines."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import os
from dataclasses import dataclass, field, InitVar
from importlib import import_module
from pathlib import Path
from typing import cast, Any, Optional, Sequence, Type

from . import exceptions as excs
from .config import SiteConfig
from .targets import Target
from .utils import import_file


class Engine(abc.ABC):

    """Object for creating site targets."""

    def __init__(
        self,
        config: SiteConfig,
        source_dirname: str = "",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.source_dirname = source_dirname
        self.config = config
        self.options = kwargs.pop("options", {})

    @property
    def source_dir(self) -> Path:
        """Path to the root source directory for this engine."""
        return self.config.sources_path / self.source_dirname

    @property
    def source_drafts_dir(self) -> Path:
        """Path to the source drafts directory for this engine."""
        return self.source_dir / self.config.drafts_dirname

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        raise NotImplementedError()


@dataclass(eq=True)
class EngineSpec:

    """Specifications of an engine in the config."""

    engine: Type[Engine] = field(init=False)

    config: SiteConfig

    source: str

    options: dict

    module: InitVar[Optional[str]]

    file: InitVar[Optional[str]]

    def __post_init__(
        self,
        module: Optional[str],
        file: Optional[str],
    ) -> None:
        match (module, file):

            case (m, None) if isinstance(m, str):
                self.engine = self._load_engine_module(self.config, m)

            case (None, f) if isinstance(f, str):
                self.engine = self._load_engine_file(self.config, f)

            case (None, None):
                msg = "one of 'module' or 'file' must be a valid string value"
                raise excs.VoltConfigError(msg)

            case (_, _):
                msg = "only one of 'module' or 'file' may be specified"
                raise excs.VoltConfigError(msg)

    def load(self) -> Engine:
        return self.engine(
            self.config, source_dirname=self.source, options=self.options
        )

    def _load_engine_module(self, config: SiteConfig, mod_spec: str) -> Type[Engine]:
        mod_name, cls_name = self._parse_class_spec(mod_spec)

        try:
            mod = import_module(mod_name)
        except ModuleNotFoundError as e:
            raise excs.VoltConfigError(f"not a valid module: {mod_name}") from e

        try:
            return cast(Type[Engine], getattr(mod, cls_name))
        except AttributeError as e:
            raise excs.VoltConfigError(
                f"engine {cls_name!r} not found in module {mod_name!r}"
            ) from e

    def _load_engine_file(self, config: SiteConfig, file_spec: str) -> Type[Engine]:
        fn, cls_name = self._parse_class_spec(file_spec)

        fp = Path(fn) if os.path.isabs(fn) else config.theme_engines_path / fn
        mod_name = f"volt.ext.theme.engines.{'.'.join(fp.parts[1:])}"
        mod = import_file(fp, mod_name)

        try:
            return cast(Type[Engine], getattr(mod, cls_name))
        except AttributeError as e:
            raise excs.VoltConfigError(
                f"engine {cls_name!r} not found in file {fn!r}"
            ) from e

    @staticmethod
    def _parse_class_spec(spec: str) -> tuple[str, str]:
        try:
            cls_loc, cls_name = spec.rsplit(":", 1)
        except ValueError:
            raise excs.VoltConfigError(f"invalid engine class specifier: {spec!r}")
        return cls_loc, cls_name
