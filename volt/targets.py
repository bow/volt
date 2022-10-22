"""Site targets."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import filecmp
from functools import cached_property
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from jinja2 import Template

from . import error as err


__all__ = [
    "collect_copy_targets",
    "CopyTarget",
    "Target",
    "TemplateTarget",
]


@dataclass(kw_only=True)
class Target(abc.ABC):

    """A single file created in the site output directory."""

    # Relative URL of the target.
    url: str

    @cached_property
    def url_parts(self) -> tuple[str, ...]:
        return tuple([part for part in self.url.split("/") if part])

    @abc.abstractmethod
    def write(self, parent_dir: Path) -> None:
        raise NotImplementedError()


@dataclass(kw_only=True)
class TemplateTarget(Target):

    """A target created by rendering from a template."""

    # Jinja2 template to use.
    template: Template

    # Render arguments.
    render_kwargs: dict

    # Source of the target.
    src: Optional[Path] = field(default=None)

    def write(self, parent_dir: Path) -> None:
        """Render the template and write it to the destination."""
        content = self.template.render(**self.render_kwargs)
        try:
            (parent_dir.joinpath(*self.url_parts)).write_text(content)
        except OSError as e:
            raise err.VoltResourceError(
                "could not write target" f" {'/'.join(self.url_parts)!r}: {e.strerror}"
            )


@dataclass(kw_only=True)
class CopyTarget(Target):

    """A target created by copying another file from the source directory."""

    # Source of the copy.
    src: Path

    # Path parts / tokens to the target.
    url_parts: tuple[str, ...]

    # Relative URL of the target.
    url: str = field(init=False)

    def __post_init__(self) -> None:
        self.url = "/".join(self.url_parts)

    def write(self, parent_dir: Path) -> None:
        """Copy the source to the destination."""
        str_src = str(self.src)
        path_dest = parent_dir.joinpath(*self.url_parts)
        str_dest = str(path_dest)
        do_copy = not path_dest.exists() or not filecmp.cmp(
            str_src, str_dest, shallow=False
        )

        if do_copy:
            try:
                shutil.copy2(str_src, str_dest)
            except OSError as e:
                raise err.VoltResourceError(
                    f"could not copy {str_src!r} to {str_dest!r}: {e.strerror}"
                )

        return None


def collect_copy_targets(start_dir: Path, invocation_dir: Path) -> list[CopyTarget]:
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
