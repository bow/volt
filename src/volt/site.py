"""Site-level functions and classes."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import fnmatch
import os
import shutil
import tempfile
from collections.abc import Callable, Generator, Iterator, Sequence
from functools import cached_property
from itertools import filterfalse, tee
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Literal,
    Optional,
    TypeVar,
    cast,
)

import structlog

from . import constants, signals
from ._import import import_file
from ._logging import log_method
from .config import Config
from .engines import Engine, MarkdownEngine
from .error import VoltResourceError
from .outputs import CopyOutput, Output, TemplateOutput
from .theme import Theme

__all__ = ["Site"]


log = structlog.get_logger(__name__)


class _PlanNode:
    """Node of the :class:`_Plan` tree."""

    __slots__ = ("path", "output", "children", "__dict__")

    def __init__(self, path: Path, output: Optional[Output] = None) -> None:
        """Initialize a plan node.

        :param path: Path to the node.
        :param output: A file to be created in the site output directory.  If set to
            ``None``, represents a directory. Otherwise, the given value must be
            an :class:`Output` instance.

        """
        self.path = path
        self.output = output
        self.children: Optional[dict[str, _PlanNode]] = (
            None if output is not None else {}
        )

    @cached_property
    def is_dir(self) -> bool:
        """Whether the node represents a directory or not."""
        return self.output is None

    def __contains__(self, value: str) -> bool:
        children = self.children or {}

        return self.is_dir and value in children

    def __iter__(self) -> Iterator["_PlanNode"]:
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
        if self.output is None:
            (build_dir / self.path).mkdir(parents=True, exist_ok=True)
            return None

        self.output.write(build_dir=build_dir)
        return None

    def add_child(self, key: str, output: Optional[Output] = None) -> None:
        """Add a child to the node.

        If a child with the given key already exists, nothing is done.

        :param str key: Key to given child.
        :param output: A file to be created in the site output directory.
            If set to ``None``, represents a directory. Otherwise, the given
            value must be a subclass of :class:`Output`.

        :raises TypeError: if the node represents a directory (does not have
            any children).

        """
        if not self.is_dir:
            raise TypeError("cannot add children to file node")
        # TODO: Adjustable behavior for outputs with the same dest? For now
        #       just take the first one.
        children = self.children or {}
        if key in children:
            return
        children[key] = _PlanNode(self.path / key, output)
        self.children = children


class _Plan:
    """The file and directory layout of the final built site.

    A plan is essentially an n-ary tree whose nodes represent either directories or
    files to be created.

    """

    def __init__(self) -> None:
        """Initialize a plan."""
        out_relpath = Path()
        self.out_relpath = out_relpath
        self._root = _PlanNode(out_relpath)
        self._root_path_len = len(out_relpath.parts)

    def add_output(self, output: Output) -> None:
        """Add an output to the plan.

        :param output: A file to be created in the site output directory.
        :param src_path: The input file used to create the output, if applicable.

        :raises ValueError:
            * when the given output's destination path is not a path relative to
              the working directory.
            * when the given output's destination path does not start with the
              project site destination path.
            * when the given output's destination path conflicts with an
              existing one

        """
        # Ensure output dest starts with project site_dest
        prefix_len = self._root_path_len
        if output.url_parts[:prefix_len] != self._root.path.parts:
            raise ValueError(
                "output destination does not start with project site destination"
            )

        rem_len = len(output.url_parts) - prefix_len
        cur = self._root

        for idx, p in enumerate(output.url_parts[prefix_len:], start=1):
            try:
                if idx < rem_len:
                    cur.add_child(p)
                    cur = cast(dict[str, _PlanNode], cur.children)[p]
                else:
                    if p in cur:
                        raise ValueError(
                            f"output path {output.url!r}"
                            + (
                                f" from input {str(src)!r}"
                                if (src := getattr(output, "src", None)) is not None
                                else ""
                            )
                            + " already added to the plan"
                        )
                    cur.add_child(p, output)
            except TypeError:
                raise ValueError(
                    f"path of output item {str(cur.path / p)!r}"
                    f" conflicts with {str(cur.path)!r}"
                ) from None

        return None

    def fnodes(self) -> Generator[_PlanNode, None, None]:
        """Yield all file output nodes, depth-first."""

        # TODO: Maybe compress the paths so we don't have to iterate over all
        #       directory parts?
        nodes = [self._root]
        while nodes:
            cur = nodes.pop()
            nodes.extend(iter(cur))
            if not cur.is_dir:
                yield cur

    def dnodes(self) -> Generator[_PlanNode, None, None]:
        """Yield the least number of directory nodes required to construct
        the site.

        In other words, yields nodes whose children all represent file outputs.

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
        self.__build_dir: Optional[Path] = None
        self.__hooks: dict[str, ModuleType] = {}

        self.config = config
        self.outputs = list[Output]()
        self.engine: Optional[Engine] = None

        self.theme = Theme.from_config(config)
        signals.send(signals.post_site_load_theme, site=self)

    def __repr__(self) -> str:
        config = self.config
        return f"{self.__class__.__name__}(name={config.name!r}, url={config.url!r})"

    @property
    def build_dir(self) -> Optional[Path]:
        """Build directory, set only just before the site is written to disk."""
        return self.__build_dir

    @log_method(with_args=True)
    def build(
        self,
        with_draft: bool,
        clean: bool,
        build_dir_prefix: str = constants.BUILD_DIR_PREFIX,
    ) -> None:
        """Build the static site in the destination directory."""

        try:
            self.__build(
                with_draft=with_draft,
                clean=clean,
                build_dir_prefix=build_dir_prefix,
            )
        finally:
            self.__hooks = {}
            signals._clear_site_signal_receivers()

    def has_output(self, pattern: str) -> bool:
        return (
            next(
                (item for item in self.outputs if fnmatch.fnmatch(item.url, pattern)),
                None,
            )
            is not None
        )

    def select_outputs(self, pattern: str) -> list[Output]:
        return [item for item in self.outputs if fnmatch.fnmatch(item.url, pattern)]

    def extract_outputs(self, pattern: str) -> list[Output]:
        matching, rest = _partition_outputs(
            self.outputs,
            lambda t: fnmatch.fnmatch(t.url, pattern),
        )
        rv = list(matching)
        self.outputs = list(rest)
        return rv

    @log_method(with_args=True)
    def __build(self, with_draft: bool, clean: bool, build_dir_prefix: str) -> None:
        """Build the static site in the destination directory."""

        self.__load_hooks()

        self.__load_engine()
        signals.send(signals.post_site_load_engines, site=self)

        self.__collect_outputs(with_draft=with_draft)
        signals.send(signals.post_site_collect_outputs, site=self)

        self.__update_render_kwargs(site=self, config=self.config, theme=self.theme)

        with tempfile.TemporaryDirectory(prefix=build_dir_prefix) as tmp_dir_name:
            build_dir = Path(tmp_dir_name)

            self.__build_dir = build_dir
            signals.send(signals.pre_site_write, site=self)
            self.__write(build_dir=build_dir, clean=clean)
            signals.send(signals.post_site_write, site=self)

            log.debug("removing build dir", path=build_dir)

        return None

    @log_method
    def __load_hooks(self) -> None:
        self.__load_hook("theme")
        self.__load_hook("project")

        return None

    @log_method
    def __load_hook(self, kind: Literal["project", "theme"]) -> None:
        config = self.config

        fp = config.hooks_module_path
        name = config.hooks_module_name

        theme = self.theme
        if kind == "theme":
            fp = theme.hooks_module_path
            name = theme.hooks_module_name

        log.debug(f"checking if {kind} hooks extension is present")
        if not fp.exists():
            log.debug(f"found no {kind} hooks extension")
            return None

        log.debug(f"loading {kind} hooks extension", path=fp, name=name)
        # NOTE: keeping a reference to the imported module to avoid garbage
        #       cleanup that would remove hooks.
        self.__hooks[kind] = import_file(fp, name)
        log.debug(f"loaded {kind} hooks extension")

        return None

    @log_method
    def __load_engine(self) -> None:
        self.engine = (
            spec.load()
            if (spec := self.theme.get_engine_spec()) is not None
            else MarkdownEngine(config=self.config, theme=self.theme)
        )

    @log_method
    def __prepare_static_outputs(self, with_draft: bool) -> list[Output]:
        config = self.config
        theme = self.theme

        outputs = {
            output.url: output
            for output in _collect_copy_outputs(theme.static_dir, config.invoc_dir)
        }

        for user_output in _collect_copy_outputs(config.static_dir, config.invoc_dir):
            url = user_output.url
            if url in outputs:
                log.warn(
                    "overwriting theme static file with user-defined static file",
                    url=url,
                )
            outputs[url] = user_output

        if with_draft:
            for draft_output in _collect_copy_outputs(
                config.draft_static_dir,
                config.invoc_dir,
            ):
                url = draft_output.url
                if url in outputs:
                    log.warn(
                        "overwriting static file with its draft version",
                        url=url,
                    )
                outputs[url] = user_output

        return list(outputs.values())

    @log_method
    def __collect_outputs(self, with_draft: bool) -> None:
        if self.engine is None:
            return None

        self.outputs = [
            *self.__prepare_static_outputs(with_draft),
            *self.engine.prepare_outputs(with_draft),
        ]

        return None

    @log_method(with_args=True)
    def __write(self, build_dir: Path, clean: bool) -> None:
        """Write all collected outputs under the destination directory."""

        plan = _Plan()
        for output in self.outputs:
            try:
                plan.add_output(output)
            except ValueError as e:
                raise VoltResourceError(f"{e}") from e

        plan.write_nodes(build_dir=build_dir)

        output_dir = self.config.output_dir
        if clean:
            shutil.rmtree(output_dir, ignore_errors=True)
        shutil.copytree(src=build_dir, dst=output_dir, dirs_exist_ok=not clean)
        # chmod if inside container to ensure host can use it as if not generated
        # from inside the container.
        if self.config.in_docker:
            for dp, _, file_names in os.walk(output_dir):
                os.chmod(dp, 0o777)  # nosec: B103
                for fn in file_names:
                    os.chmod(os.path.join(dp, fn), 0o666)  # nosec: B103

        return None

    def __update_render_kwargs(self, **kwargs: Any) -> None:
        for output in self.outputs:
            if not isinstance(output, TemplateOutput):
                continue
            output.render_kwargs.update(**kwargs)


T = TypeVar("T")


def _partition_outputs(
    outputs: Sequence[T],
    pred: Callable[[T], bool],
) -> tuple[Iterator[T], Iterator[T]]:
    iter1, iter2 = tee(outputs)
    matching = filter(pred, iter1)
    rest = filterfalse(pred, iter2)
    return matching, rest


def _calc_relpath(output: Path, ref: Path) -> Path:
    """Calculate the output's path relative to the reference.

    :param output: The path to which the relative path will point.
    :param ref: Reference path.

    :returns: The relative path from ``ref`` to ``to``.

    :raises ValueError: when one of the given input paths is not an absolute
        path.

    """
    ref = ref.expanduser()
    output = output.expanduser()
    if not ref.is_absolute() or not output.is_absolute():
        raise ValueError("could not compute relative paths of non-absolute input paths")

    common = Path(os.path.commonpath([ref, output]))
    common_len = len(common.parts)
    ref_uniq = ref.parts[common_len:]
    output_uniq = output.parts[common_len:]

    rel_parts = ("..",) * (len(ref_uniq)) + output_uniq

    return Path(*rel_parts)


def _collect_copy_outputs(start_dir: Path, invocation_dir: Path) -> list[CopyOutput]:
    """Gather files from the given start directory recursively as copy outputs."""

    src_relpath = _calc_relpath(start_dir, invocation_dir)
    src_rel_len = len(src_relpath.parts)

    outputs: list[CopyOutput] = []

    try:
        entries = list(os.scandir(src_relpath))
    except FileNotFoundError:
        return outputs
    else:
        while entries:
            de = entries.pop()
            if de.is_dir():
                entries.extend(os.scandir(de))
            else:
                dtoks = Path(de.path).parts[src_rel_len:]
                outputs.append(CopyOutput(src=Path(de.path), url_parts=dtoks))

        return outputs
