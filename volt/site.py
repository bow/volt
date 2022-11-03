"""Site-level functions and classes."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import fnmatch
import os
import shutil
import tempfile
from contextlib import suppress
from functools import cached_property
from itertools import filterfalse, tee
from pathlib import Path
from typing import (
    cast,
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    Optional,
    Sequence,
    TypeVar,
)

import structlog

from . import constants, signals
from .config import Config
from .engines import Engine, MarkdownEngine, StaticEngine
from .error import VoltResourceError
from .targets import Target, TemplateTarget
from .theme import Theme
from ._import import import_file
from ._logging import log_method


__all__ = ["Plan", "PlanNode", "Site"]


log = structlog.get_logger(__name__)


class PlanNode:

    """Node of the :class:`Plan` tree."""

    __slots__ = ("path", "target", "children", "__dict__")

    def __init__(self, path: Path, target: Optional[Target] = None) -> None:
        """Initialize a plan node.

        :param path: Path to the node.
        :param A target to be created in the site output directory.  If set to
            ``None``, represents a directory. Otherwise, the given value must be
            a subclass of :class:`Target`.

        """
        self.path = path
        self.target = target
        self.children: Optional[Dict[str, PlanNode]] = (
            None if target is not None else {}
        )

    @cached_property
    def is_dir(self) -> bool:
        """Whether the node represents a directory or not."""
        return self.target is None

    def __contains__(self, value: str) -> bool:
        children = self.children or {}

        return self.is_dir and value in children

    def __iter__(self) -> Iterator["PlanNode"]:
        if not self.is_dir:
            return iter([])
        children = self.children or {}

        return iter(children.values())

    def create(self, build_dir: Path) -> None:
        """Write the node to the filesystem.

        If the node represents a directory, the directory and its parents will
        be created. If it represents a file, the file will be written. The
        latter assumes that all parent directories of the file already exists.

        """
        if self.target is None:
            (build_dir / self.path).mkdir(parents=True, exist_ok=True)
            return None

        self.target.write(build_dir=build_dir)
        return None

    def add_child(self, key: str, target: Optional[Target] = None) -> None:
        """Add a child to the node.

        If a child with the given key already exists, nothing is done.

        :param str key: Key to given child.
        :param target: A target to be created in the site output directory.
            If set to ``None``, represents a directory. Otherwise, the given
            value must be a subclass of :class:`Target`.

        :raises TypeError: if the node represents a directory (does not have
            any children).

        """
        if not self.is_dir:
            raise TypeError("cannot add children to file node")
        # TODO: Adjustable behavior for targets with the same dest? For now
        #       just take the first one.
        children = self.children or {}
        if key in children:
            return
        children[key] = PlanNode(self.path / key, target)
        self.children = children


class Plan:

    """The file and directory layout of the final built site.

    A plan is essentially an n-ary tree whose nodes represent either directories or
    files to be created.

    """

    def __init__(self) -> None:
        """Initialize a plan."""
        out_relpath = Path()
        self.out_relpath = out_relpath
        self._root = PlanNode(out_relpath)
        self._root_path_len = len(out_relpath.parts)

    def add_target(self, target: Target) -> None:
        """Add a target to the plan.

        :param target: A target to be created in the site output directory.
        :param src_path: The source file of the target, if applicable.

        :raises ValueError:
            * when the given target's destination path is not a path relative to
              the working directory.
            * when the given target's destination path does not start with the
              project site destination path.
            * when the given target's destination path conflicts with an
              existing one

        """
        # Ensure target dest starts with project site_dest
        prefix_len = self._root_path_len
        if target.url_parts[:prefix_len] != self._root.path.parts:
            raise ValueError(
                "target destination does not start with project site destination"
            )

        rem_len = len(target.url_parts) - prefix_len
        cur = self._root

        for idx, p in enumerate(target.url_parts[prefix_len:], start=1):
            try:
                if idx < rem_len:
                    cur.add_child(p)
                    cur = cast(Dict[str, PlanNode], cur.children)[p]
                else:
                    if p in cur:
                        raise ValueError(
                            f"target path {target.url!r}"
                            + (
                                f" from source {str(src)!r}"
                                if (src := getattr(target, "src", None)) is not None
                                else ""
                            )
                            + " already added to the plan"
                        )
                    cur.add_child(p, target)
            except TypeError:
                raise ValueError(
                    f"path of target item {str(cur.path / p)!r}"
                    f" conflicts with {str(cur.path)!r}"
                ) from None

        return None

    def fnodes(self) -> Generator[PlanNode, None, None]:
        """Yield all file target nodes, depth-first."""

        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self) -> Generator[PlanNode, None, None]:
        """Yield the least number of directory nodes required to construct
        the site.

        In other words, yields nodes whose children all represent file targets.

        """
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            children = list(iter(cur))
            fnodes = [c for c in children if not c.is_dir]
            if children and len(fnodes) == len(children):
                yield cur
            else:
                nodes.extend(children)

    def write_nodes(self, build_dir: Path) -> None:
        """Write the plan nodes according to the plan under the given parent
        directory."""

        for dn in self.dnodes():
            dn.create(build_dir=build_dir)

        for fn in self.fnodes():
            fn.create(build_dir=build_dir)

        return None


class Site:

    """The static site."""

    def __init__(self, config: Config) -> None:
        """Initialize the static site for building.

        :param config: The validated site configuration.

        """
        self.config = config
        self.targets = list[Target]()
        self.engines = list[Engine]()
        self.theme = Theme.from_config(config)

    def __repr__(self) -> str:
        config = self.config
        return f"{self.__class__.__name__}(name={config.name!r}, url={config.url!r})"

    @log_method
    def load_hooks(self) -> None:

        config = self.config
        log.debug("checking if project hooks extension is present")
        fp = config.hooks_module_path

        if fp is None:
            log.debug("found no project hooks extension")
            return None

        log.debug("loading project hooks extension", path=fp)
        # NOTE: keeping a reference to the imported module to avoid garbage
        #       cleanup that would remove hooks.
        self.__hooks = import_file(fp, config.hooks_module_name)
        log.debug("loaded project hooks extension")

        return None

    @log_method
    def load_engines(self) -> None:

        log.debug("loading theme engines")
        engines: Optional[list[Engine]] = self.theme.load_engines()
        log.debug(
            "loaded theme engines",
            engines=[engine.name for engine in (engines or [])],
        )

        # Add MarkdownEngine if no engines are loaded.
        if not engines:
            log.debug("adding MarkdownEngine to loaded engines")
            engines = [MarkdownEngine(config=self.config, theme=self.theme)]

        # Add StaticEngine if not already added.
        if not any(engine.__class__ is StaticEngine for engine in engines):
            log.debug("adding StaticEngine to loaded engines")
            engines.insert(0, StaticEngine(config=self.config, theme=self.theme))

        self.engines = engines
        log.debug(
            "loaded all site engines",
            engines=[engine.name for engine in engines],
        )

    @log_method
    def collect_targets(self) -> None:
        self.targets = [
            target for engine in self.engines for target in engine.create_targets()
        ]
        return None

    @log_method(with_args=True)
    def write(self, build_dir: Path, clean: bool) -> None:
        """Write all collected targets under the destination directory."""

        plan = Plan()
        for target in self.targets:
            try:
                plan.add_target(target)
            except ValueError as e:
                raise VoltResourceError(f"{e}") from e

        plan.write_nodes(build_dir=build_dir)

        target_dir = self.config.target_dir
        if clean:
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(src=build_dir, dst=target_dir)
        # chmod if inside container to ensure host can use it as if not generated
        # from inside the container.
        if self.config.in_docker:
            for dp, _, fnames in os.walk(target_dir):
                os.chmod(dp, 0o777)  # nosec: B103
                for fn in fnames:
                    os.chmod(os.path.join(dp, fn), 0o666)  # nosec: B103

        return None

    @log_method(with_args=True)
    def build(
        self,
        clean: bool = True,
        build_dir_prefix: str = constants.BUILD_DIR_PREFIX,
    ) -> None:
        """Build the static site in the destination directory."""

        self.load_hooks()

        self.load_engines()
        signals.send(signals.post_site_load_engines, site=self)

        self.collect_targets()
        signals.send(signals.post_site_collect_targets, site=self)

        self.update_render_kwargs(site=self, config=self.config)

        with tempfile.TemporaryDirectory(prefix=build_dir_prefix) as tmp_dir_name:
            build_dir = Path(tmp_dir_name)
            signals.send(signals.pre_site_write, site=self, build_dir=build_dir)
            self.write(build_dir=build_dir, clean=clean)
            log.debug("removing build dir", path=build_dir)

        return None

    def update_render_kwargs(self, **kwargs: Any) -> None:
        for target in self.targets:
            if not isinstance(target, TemplateTarget):
                continue
            target.render_kwargs.update(**kwargs)

    def select_targets(self, pattern: str) -> list[Target]:
        return [
            target for target in self.targets if fnmatch.fnmatch(target.url, pattern)
        ]

    def extract_targets(self, pattern: str) -> list[Target]:
        matching, rest = _partition_targets(
            self.targets,
            lambda t: fnmatch.fnmatch(t.url, pattern),
        )
        rv = list(matching)
        self.targets = list(rest)
        return rv

    @log_method
    def _cleanup(self) -> None:
        with suppress(AttributeError):
            del self.__hooks
        signals._clear()


T = TypeVar("T")


def _partition_targets(
    targets: Sequence[T],
    pred: Callable[[T], bool],
) -> tuple[Iterator[T], Iterator[T]]:
    iter1, iter2 = tee(targets)
    matching = filter(pred, iter1)
    rest = filterfalse(pred, iter2)
    return matching, rest
