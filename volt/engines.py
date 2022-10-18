"""Site engines."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import os
from dataclasses import dataclass, field, InitVar
from importlib import import_module
from pathlib import Path
from typing import cast, Any, Optional, Sequence, Type

from jinja2 import Template

from . import exceptions as excs
from .config import SiteConfig
from .constants import MARKDOWN_EXT
from .sources import MarkdownSource
from .targets import Target
from .theme import Theme
from .utils import import_file


class Engine(abc.ABC):

    """Object for creating site targets."""

    def __init__(
        self,
        site_config: SiteConfig,
        theme: Theme,
        source_dirname: str = "",
        opts: Optional[dict] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.site_config = site_config
        self.theme = theme
        self.source_dirname = source_dirname
        self.opts = opts or {}

    @property
    def source_dir(self) -> Path:
        """Path to the root source directory for this engine."""
        return self.site_config.sources_dir / self.source_dirname

    @property
    def source_drafts_dir(self) -> Path:
        """Path to the source drafts directory for this engine."""
        return self.source_dir / self.site_config.drafts_dirname

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        raise NotImplementedError()


@dataclass(eq=True)
class EngineSpec:

    """Specifications of an engine in the config."""

    engine: Type[Engine] = field(init=False)

    site_config: SiteConfig

    theme: Theme

    source: str

    opts: dict

    module: InitVar[Optional[str]]

    file: InitVar[Optional[str]]

    def __post_init__(
        self,
        module: Optional[str],
        file: Optional[str],
    ) -> None:
        match (module, file):

            case (m, None) if isinstance(m, str):
                self.engine = self._load_engine_module(m)

            case (None, f) if isinstance(f, str):
                self.engine = self._load_engine_file(self.theme, f)

            case (None, None):
                msg = "one of 'module' or 'file' must be a valid string value"
                raise excs.VoltConfigError(msg)

            case (_, _):
                msg = "only one of 'module' or 'file' may be specified"
                raise excs.VoltConfigError(msg)

    def load(self) -> Engine:
        return self.engine(
            site_config=self.site_config,
            theme=self.theme,
            source_dirname=self.source,
            opts=self.opts,
        )

    def _load_engine_module(self, mod_spec: str) -> Type[Engine]:
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

    def _load_engine_file(self, theme: Theme, file_spec: str) -> Type[Engine]:
        fn, cls_name = self._parse_class_spec(file_spec)

        fp = Path(fn) if os.path.isabs(fn) else theme.path / fn
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


class MarkdownEngine(Engine):

    """Engine that creates HTML targets from Markdown sources."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        template_name = self.opts.pop("template_name", "page")
        try:
            self.template = self.theme.load_template(template_name)
        except excs.VoltMissingTemplateError:
            default_fp = Path(__file__).parent / "defaults" / f"{template_name}.html.j2"
            self.template = Template(default_fp.read_text())

    def create_targets(self) -> Sequence[Target]:

        config = self.site_config
        get_sources = self.get_sources

        fps = get_sources() + (get_sources(drafts=True) if config.with_drafts else [])

        targets = [
            MarkdownSource.from_path(
                src=fp,
                template=self.template,
                site_config=config,
                is_draft=is_draft,
            ).target
            for fp, is_draft in fps
        ]

        return targets

    def get_sources(self, drafts: bool = False) -> list[tuple[Path, bool]]:
        eff_dir = self.source_dir if not drafts else self.source_drafts_dir
        return [(p, drafts) for p in eff_dir.glob(f"*{MARKDOWN_EXT}")]
