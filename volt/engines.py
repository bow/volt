"""Site engines."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import abc
import os
from dataclasses import dataclass, field, InitVar
from importlib import import_module
from pathlib import Path
from typing import cast, Any, Optional, Sequence, Type

import structlog
from jinja2 import Template

from . import error as err
from .config import Config
from .constants import MARKDOWN_EXT, STATIC_DIR_NAME
from .sources import Markdown2Source
from .targets import CopyTarget, Target, TemplateTarget
from .theme import Theme
from ._import import import_file
from ._logging import log_method


__all__ = ["Engine", "EngineSpec", "Markdown2Engine", "StaticEngine"]


log = structlog.get_logger(__name__)


class Engine(abc.ABC):

    """Object for creating site targets."""

    def __init__(
        self,
        id: str,
        config: Config,
        theme: Theme,
        source_dir_name: str = "",
        opts: Optional[dict] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.id = id
        self.config = config
        self.theme = theme
        self.source_dir_name = source_dir_name
        self.opts = opts or {}

    @property
    def name(self) -> str:
        """Name of the engine class."""
        return self.__class__.__name__

    @property
    def source_dir(self) -> Path:
        """Path to the root source directory for this engine."""
        return self.config.sources_dir / self.source_dir_name

    @property
    def source_drafts_dir(self) -> Path:
        """Path to the source drafts directory for this engine."""
        return self.source_dir / self.config.drafts_dir_name

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        raise NotImplementedError()


@dataclass(eq=True, repr=True)
class EngineSpec:

    """Specifications of an engine in the config."""

    id: str
    source: str
    opts: dict
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

    def load(self) -> Engine:
        return self.engine(
            id=self.id,
            config=self.config,
            theme=self.theme,
            source_dir_name=self.source,
            opts=self.opts,
        )

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

        fp = theme.engines_module_path
        if not fp.exists():
            raise err.VoltConfigError("theme engines file not found")

        mod_name = theme.engines_module_name

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


class StaticEngine(Engine):

    """Engine that resolves and copies static files."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if (kwargs.get("source_dir_name") or STATIC_DIR_NAME) != STATIC_DIR_NAME:
            raise err.VoltConfigError(
                f"if specified, 'source' must be {STATIC_DIR_NAME!r} for {self.name}"
            )
        kwargs["source_dir_name"] = STATIC_DIR_NAME
        super().__init__(*args, **kwargs)

    @property
    def source_drafts_dir(self) -> Path:
        log.warn(f"drafts directory is not applicable to {self.name}")
        return self.source_dir

    def create_targets(self) -> Sequence[CopyTarget]:
        config = self.config
        theme = self.theme

        targets = {
            target.url: target
            for target in _collect_copy_targets(theme.static_dir, config.invoc_dir)
        }

        for user_target in _collect_copy_targets(config.static_dir, config.invoc_dir):
            url = user_target.url
            if url in targets:
                log.warn("using user-defined target instead of theme target", url=url)
            targets[url] = user_target

        return list(targets.values())


class Markdown2Engine(Engine):

    """Engine that creates HTML targets using the markdown2 library."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        template_name = self.opts.pop("template_name", "page.html.j2")
        try:
            self.template = self.theme.load_template_file(template_name)
        except err.VoltMissingTemplateError:
            default_fp = Path(__file__).parent / "defaults" / f"{template_name}"
            self.template = Template(default_fp.read_text())

    def create_targets(self) -> Sequence[TemplateTarget]:

        config = self.config
        get_sources = self.get_sources

        fps = get_sources() + (get_sources(drafts=True) if config.with_drafts else [])

        targets = [
            Markdown2Source.from_path(
                src=fp, config=config, is_draft=is_draft
            ).to_template_target(self.template)
            for fp, is_draft in fps
        ]

        return targets

    def get_sources(self, drafts: bool = False) -> list[tuple[Path, bool]]:
        eff_dir = self.source_dir if not drafts else self.source_drafts_dir
        return [(p, drafts) for p in eff_dir.glob(f"*{MARKDOWN_EXT}")]


def _collect_copy_targets(start_dir: Path, invocation_dir: Path) -> list[CopyTarget]:
    """Gather files from the given start directory recursively as copy targets."""

    src_relpath = _calc_relpath(start_dir, invocation_dir)
    src_rel_len = len(src_relpath.parts)

    targets: list[CopyTarget] = []
    entries = list(os.scandir(src_relpath))
    while entries:
        de = entries.pop()
        if de.is_dir():
            entries.extend(os.scandir(de))
        else:
            dtoks = Path(de.path).parts[src_rel_len:]
            targets.append(CopyTarget(src=Path(de.path), url_parts=dtoks))

    return targets


def _calc_relpath(target: Path, ref: Path) -> Path:
    """Calculate the target's path relative to the reference.

    :param target: The path to which the relative path will point.
    :param ref: Reference path.

    :returns: The relative path from ``ref`` to ``to``.

    :raises ValueError: when one of the given input paths is not an absolute
        path.

    """
    ref = ref.expanduser()
    target = target.expanduser()
    if not ref.is_absolute() or not target.is_absolute():
        raise ValueError("could not compute relative paths of non-absolute input paths")

    common = Path(os.path.commonpath([ref, target]))
    common_len = len(common.parts)
    ref_uniq = ref.parts[common_len:]
    target_uniq = target.parts[common_len:]

    rel_parts = ("..",) * (len(ref_uniq)) + target_uniq

    return Path(*rel_parts)
