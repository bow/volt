"""Site-level functions and classes."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import os
import shutil
import tempfile
from contextlib import suppress
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Dict, Generator, Iterator, Optional, Sequence, cast


from . import constants
from .config import SiteConfig
from .exceptions import VoltConfigError, VoltResourceError
from .engines import Engine
from .targets import CopyTarget, Target
from .utils import calc_relpath, import_file

__all__ = ["Site", "SiteNode", "SitePlan"]


class SiteNode:

    """Node of the :class:`SitePlan` tree."""

    __slots__ = ("path", "target", "children", "__dict__")

    def __init__(self, path: Path, target: Optional[Target] = None) -> None:
        """Initialize a site node.

        :param path: Path to the node.
        :param A target to be created in the site output directory.  If set to
            ``None``, represents a directory. Otherwise, the given value must be
            a subclass of :class:`Target`.

        """
        self.path = path
        self.target = target
        self.children: Optional[Dict[str, SiteNode]] = (
            None if target is not None else {}
        )

    @cached_property
    def is_dir(self) -> bool:
        """Whether the node represents a directory or not."""
        return self.target is None

    def __contains__(self, value: str) -> bool:
        children = self.children or {}

        return self.is_dir and value in children

    def __iter__(self) -> Iterator["SiteNode"]:
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
        children[key] = SiteNode(self.path / key, target)
        self.children = children


class SitePlan:

    """The file and directory layout of the final built site.

    A site plan is essentially an n-ary tree whose nodes represent either
    directories or files to be created.

    """

    def __init__(self) -> None:
        """Initialize a site plan."""
        out_relpath = Path()
        self.out_relpath = out_relpath
        self._root = SiteNode(out_relpath)
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
        if target.path_parts[:prefix_len] != self._root.path.parts:
            raise ValueError(
                "target destination does not start with project site destination"
            )

        rem_len = len(target.path_parts) - prefix_len
        cur = self._root

        for idx, p in enumerate(target.path_parts[prefix_len:], start=1):
            try:
                if idx < rem_len:
                    cur.add_child(p)
                    cur = cast(Dict[str, SiteNode], cur.children)[p]
                else:
                    if p in cur:
                        raise ValueError(
                            f"target path {('/'.join(target.path_parts))!r}"
                            + (
                                f" from source {str(target.src)!r}"
                                if target.src is not None
                                else ""
                            )
                            + " already added to the site plan"
                        )
                    cur.add_child(p, target)
            except TypeError:
                raise ValueError(
                    f"path of target item {str(cur.path / p)!r}"
                    f" conflicts with {str(cur.path)!r}"
                ) from None

        return None

    def fnodes(self) -> Generator[SiteNode, None, None]:
        """Yield all file target nodes, depth-first."""

        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self) -> Generator[SiteNode, None, None]:
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
        """Write the site nodes according to the plan under the given parent
        directory."""

        for dn in self.dnodes():
            dn.create(parent_dir=parent_dir)

        for fn in self.fnodes():
            fn.create(parent_dir=parent_dir)

        return None


class Site:

    """The static site."""

    def __init__(self, config: SiteConfig) -> None:
        """Initialize the static site for building.

        :param config: The validated site configuration.

        """
        self.config = config

    def _gather_copy_targets(self, targets_dir: Path) -> Sequence[CopyTarget]:
        """Add files from the given targets directory into the site plan."""

        config = self.config
        src_relpath = calc_relpath(targets_dir, config.cwd)
        src_rel_len = len(src_relpath.parts)

        targets: list[CopyTarget] = []
        entries = list(os.scandir(src_relpath))
        while entries:
            de = entries.pop()
            if de.is_dir():
                entries.extend(os.scandir(de))
            else:
                dtoks = Path(de.path).parts[src_rel_len:]
                targets.append(CopyTarget(src=Path(de.path), path_parts=dtoks))

        return targets

    def _run_engine(self, fp: Path, cls_name: str, options: dict) -> Sequence[Target]:
        """Run a given engine defined in the given path"""

        cfg = self.config
        # TODO: Replace this with a pattern less prone to name collision
        mod = import_file(fp, f"volt.ext.theme.engines.{fp.stem}")

        eng_cls = getattr(mod, cls_name, None)
        if eng_cls is None:
            return []

        eng = cast(Engine, eng_cls(cfg, options=options))
        targets = eng.create_targets()

        return targets

    def gather_static_targets(self) -> list[CopyTarget]:
        """Create :class:`CopyTarget` instances representing targets copied from
        the site and theme static directories."""
        cfg = self.config

        targets: list[CopyTarget] = []
        for static_path in (cfg.static_path, cfg.theme_static_path):
            targets.extend(self._gather_copy_targets(targets_dir=static_path))

        return targets

    def generate_engine_targets(self) -> list[Target]:
        """Run user-defined engines and generate their targets."""

        cfg = self.config
        engines = cfg.get("theme", {}).get("engines", [])

        targets: list[Target] = []

        for entry in engines:
            if (cls_loc := entry.get("class", None)) is None:
                continue
            try:
                cls_fn, cls_name = cls_loc.rsplit(":", 1)
            except ValueError:
                raise VoltConfigError("invalid engine class specifier: {cls_loc!r}")

            cls_fp = cfg.theme_engines_path / cls_fn
            targets.extend(self._run_engine(cls_fp, cls_name, entry.get("options", {})))

        return targets

    def build(self, clean: bool = True) -> None:
        """Build the static site in the destination directory."""

        with tempfile.TemporaryDirectory(
            prefix=constants.BUILD_DIR_PREFIX
        ) as tmp_dir_name:

            plan = SitePlan()
            for target in chain(
                self.gather_static_targets(), self.generate_engine_targets()
            ):
                try:
                    plan.add_target(target)
                except ValueError as e:
                    raise VoltResourceError(f"{e}") from e

            build_path = Path(tmp_dir_name)
            plan.write_nodes(parent_dir=build_path)

            out_path = self.config.out_path
            if clean:
                with suppress(FileNotFoundError):
                    shutil.rmtree(out_path)
            shutil.copytree(src=build_path, dst=out_path)
            # chmod if inside container to ensure host can use it as if not generated
            # from inside the container.
            if self.config.in_docker:
                for dp, _, fnames in os.walk(out_path):
                    os.chmod(dp, 0o777)  # nosec: B103
                    for fn in fnames:
                        os.chmod(os.path.join(dp, fn), 0o666)  # nosec: B103

        return None
