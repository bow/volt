"""Site outputs."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import abc
import filecmp
from functools import cached_property
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from jinja2 import Template

from . import error as err


__all__ = [
    "CopyOutput",
    "FileOutput",
    "Output",
    "TemplateOutput",
]


@dataclass(kw_only=True)
class Output(abc.ABC):

    """A single file created in the site output directory."""

    # Relative URL of the output.
    url: str

    @cached_property
    def url_parts(self) -> tuple[str, ...]:
        return tuple([part for part in self.url.split("/") if part])

    @abc.abstractmethod
    def write(self, build_dir: Path) -> None:
        raise NotImplementedError()


@dataclass(kw_only=True)
class FileOutput(Output):

    """A single file to be written with contents from memory."""

    contents: str | bytes

    def write(self, build_dir: Path) -> None:
        fp = build_dir.joinpath(*self.url_parts)
        contents = self.contents

        try:
            if isinstance(contents, str):
                fp.write_text(contents)
            elif isinstance(contents, bytes):
                fp.write_bytes(contents)
            else:
                raise ValueError(f"unexpected content type: '{type(contents)}'")
        except OSError as e:
            raise err.VoltResourceError(
                f"could not write output {self.url!r}: {e.strerror}"
            )


@dataclass(kw_only=True)
class TemplateOutput(Output):

    """An output created by rendering from a template."""

    # Jinja2 template to use.
    template: Template

    # Render arguments.
    render_kwargs: dict = field(repr=False)

    # Input used to generate the template output.
    src: Optional[Path] = field(default=None)

    def write(self, build_dir: Path) -> None:
        """Render the template and write it to the destination."""
        content = self.template.render(**{"meta": {}, **self.render_kwargs})
        try:
            (build_dir.joinpath(*self.url_parts)).write_text(content)
        except OSError as e:
            raise err.VoltResourceError(
                f"could not write output {self.url!r}: {e.strerror}"
            )


@dataclass(kw_only=True)
class CopyOutput(Output):

    """An output created by copying a file from the contents directory."""

    # Source of the copy.
    src: Path

    # Path parts / tokens to the output.
    url_parts: tuple[str, ...]

    # Relative URL of the output.
    url: str = field(init=False)

    def __post_init__(self) -> None:
        self.url = f"/{'/'.join(self.url_parts)}"

    def write(self, build_dir: Path) -> None:
        """Copy the source to the destination."""
        str_src = str(self.src)
        path_dest = build_dir.joinpath(*self.url_parts)
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
