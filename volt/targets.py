"""Site targets."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import filecmp
from functools import cached_property
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from jinja2 import Template

from . import error as err
from .utils import calc_relpath


class Target(abc.ABC):

    """A single file created in the site output directory."""

    # Relative URL of the target.
    url: str

    # Source of the target.
    src: Optional[Path]

    @cached_property
    def url_parts(self) -> tuple[str, ...]:
        return tuple([part for part in self.url.split("/") if part])

    @abc.abstractmethod
    def write(self, parent_dir: Path) -> None:
        raise NotImplementedError()


@dataclass(frozen=True)
class TemplateTarget(Target):

    """A target created by rendering from a template."""

    # URL of the target.
    url: str

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


@dataclass(frozen=True)
class CopyTarget(Target):

    """A target created by copying another file from the source directory."""

    # Filesystem path to the source.
    src: Path

    # Path parts / tokens to the target.
    url_parts: Tuple[str, ...]

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

    src_relpath = calc_relpath(start_dir, invocation_dir)
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
