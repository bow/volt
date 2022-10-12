"""Site targets."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import filecmp
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from jinja2 import Template

from . import exceptions as excs


class Target(abc.ABC):

    """A single file created in the site output directory."""

    # Path parts / tokens to the target.
    path_parts: Tuple[str, ...]

    # Source of the target.
    src: Optional[Path]

    @abc.abstractmethod
    def write(self, parent_dir: Path) -> None:
        raise NotImplementedError()


@dataclass(frozen=True)
class TemplateTarget(Target):

    """A target created by rendering from a template."""

    # Jinja2 template to use.
    template: Template

    # Render arguments.
    render_kwargs: dict

    # Path parts / tokens to the target.
    path_parts: Tuple[str, ...]

    # Source of the target.
    src: Optional[Path] = field(default=None)

    def write(self, parent_dir: Path) -> None:
        """Render the template and write it to the destination."""
        content = self.template.render(**self.render_kwargs)
        try:
            (parent_dir.joinpath(*self.path_parts)).write_text(content)
        except OSError as e:
            raise excs.VoltResourceError(
                "could not write target" f" {'/'.join(self.path_parts)!r}: {e.strerror}"
            )


@dataclass(frozen=True)
class CopyTarget(Target):

    """A target created by copying another file from the source directory."""

    # Filesystem path to the source.
    src: Path

    # Path parts / tokens to the target.
    path_parts: Tuple[str, ...]

    def write(self, parent_dir: Path) -> None:
        """Copy the source to the destination."""
        str_src = str(self.src)
        path_dest = parent_dir.joinpath(*self.path_parts)
        str_dest = str(path_dest)
        do_copy = not path_dest.exists() or not filecmp.cmp(
            str_src, str_dest, shallow=False
        )

        if do_copy:
            try:
                shutil.copy2(str_src, str_dest)
            except OSError as e:
                raise excs.VoltResourceError(
                    f"could not copy {str_src!r} to {str_dest!r}: {e.strerror}"
                )

        return None
