"""Site-level functions and classes."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
import shutil
import tempfile
from functools import cached_property
from pathlib import Path
from typing import Dict, Generator, Iterator, Optional, Sequence, cast

import structlog

from . import constants, signals
from .config import Config
from .engines import MarkdownEngine
from .error import VoltResourceError
from .targets import collect_copy_targets, Target
from .theme import Theme
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

    def create(self, parent_dir: Path) -> None:
        """Write the node to the filesystem.

        If the node represents a directory, the directory and its parents will
        be created. If it represents a file, the file will be written. The
        latter assumes that all parent directories of the file already exists.

        """
        if self.target is None:
            (parent_dir / self.path).mkdir(parents=True, exist_ok=True)
            return None

        self.target.write(parent_dir=parent_dir)
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

    def write_nodes(self, parent_dir: Path) -> None:
        """Write the plan nodes according to the plan under the given parent
        directory."""

        for dn in self.dnodes():
            dn.create(parent_dir=parent_dir)

        for fn in self.fnodes():
            fn.create(parent_dir=parent_dir)

        return None


class Site:

    """The static site."""

    def __init__(self, config: Config) -> None:
        """Initialize the static site for building.

        :param config: The validated site configuration.

        """
        self.config = config
        self.theme = Theme.from_site_config(config)
        self.targets: Sequence[Target] = []

    @log_method
    def collect_targets(self) -> None:
        static_targets = self.theme.collect_static_targets() + collect_copy_targets(
            self.config.static_dir, self.config.invoc_dir
        )

        engines = (
            engs
            if (engs := self.theme.load_engines()) is not None
            else [MarkdownEngine(config=self.config, source_dirname="")]
        )

        targets = static_targets + [
            target for engine in engines for target in engine.create_targets()
        ]

        self.targets = targets

        return None

    @log_method
    def write(
        self,
        clean: bool,
        build_dir_prefix: str = constants.BUILD_DIR_PREFIX,
    ) -> None:
        """Write all collected targets under the destination directory."""

        with tempfile.TemporaryDirectory(prefix=build_dir_prefix) as tmp_dir_name:

            plan = Plan()
            for target in self.targets:
                try:
                    plan.add_target(target)
                except ValueError as e:
                    raise VoltResourceError(f"{e}") from e

            build_dir = Path(tmp_dir_name)
            plan.write_nodes(parent_dir=build_dir)

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

    @log_method
    def build(self, clean: bool = True) -> None:
        """Build the static site in the destination directory."""

        self.collect_targets()
        signals.send(signals.post_site_collect_targets, site=self)

        signals.send(signals.pre_site_write, site=self)
        self.write(clean=clean)

        return None
