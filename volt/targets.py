# -*- coding: utf-8 -*-
"""
    volt.targets
    ~~~~~~~~~~~~

    Target-related classses and functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import abc
import filecmp
import shutil
from pathlib import Path

import jinja2.exceptions as j2exc
from jinja2 import Template

from .units import Unit
from .utils import Result

__all__ = ["CopyTarget", "PageTarget", "Target"]


class Target:

    """A file created in the site output directory."""

    @property
    @abc.abstractmethod
    def dest(self) -> Path:
        """Path to the target, relative to the working directory."""
        raise NotImplementedError

    @abc.abstractmethod
    def create(self) -> Result[None]:
        """Create the target at the destination."""
        raise NotImplementedError


class PageTarget(Target):

    """A target created by writing text contents."""

    __slots__ = ("src", "_dest", "contents")

    @classmethod
    def from_template(
        cls,
        src: Unit,
        dest: Path,
        template: Template,
    ) -> Result["PageTarget"]:
        """Create a :class:`PageTarget` instance from a jinja2 template.

        :param src: Source unit containing the data for templating.
        :param dest: Path to the file to write, relative to the directory from
            which Volt is invoked.
        :param template: Jinja2 template instance to use.

        :returns: The page target instance or an error message indicating
            failure.

        """
        try:
            contents = template.render(unit=src)
        except j2exc.UndefinedError as e:
            return Result.as_failure(
                f"cannot render to {str(dest)!r}"  # type: ignore
                f" using {template.name!r}:"
                f" {e.message}")

        return Result.as_success(cls(src, dest, contents))

    def __init__(self, src: Unit, dest: Path, contents: str) -> None:
        """Initialize a page target.

        :param src: Source unit containing the data of the target.
        :param dest: Path to the file to write, relative to the directory from
            which Volt is invoked.
        :param contents: The text contents to be written.

        """
        self.src = src
        self._dest = dest
        self.contents = contents

    @property
    def dest(self) -> Path:
        """Where the page will be written."""

        return self._dest

    @property
    def metadata(self) -> dict:
        """The metadata of the unit source."""

        return self.src.metadata

    def create(self) -> Result[None]:
        """Write the text contents to the destination.

        :returns: Nothing when the write succeeds or an error message indicating
            failure.

        """
        # TODO: check cache?
        try:
            self.dest.write_text(self.contents)
        except OSError as e:
            return Result.as_failure(
                f"cannot write target {str(self.dest)!r}: {e.strerror}"
            )

        return Result.as_success(None)


class CopyTarget(Target):

    """A target created by copying files."""

    __slots__ = ("src", "_dest")

    def __init__(self, src: Path, dest: Path) -> None:
        """Initialize a copy target.

        :param src: Path to the copy source, relative to the directory from
            which Volt is invoked.
        :param dest: Path to the copy destination, relative to the directory
            from which Volt is invoked.

        """
        self.src = src
        self._dest = dest

    @property
    def dest(self) -> Path:
        """The copy destination."""
        return self._dest

    def create(self) -> Result[None]:
        """Copy the source to the destination.

        The copy is performed only if the destination does not yet exist or,
        if it exists, if the contents are different.

        :returns: Nothing when the copy succeeds or an error message indicating
            failure.

        """
        str_src = str(self.src)
        str_dest = str(self.dest)
        do_copy = (
            not self.dest.exists()
            or not filecmp.cmp(str_src, str_dest, shallow=False)
        )

        if do_copy:
            try:
                shutil.copy2(str_src, str_dest)
            except OSError as e:
                return Result.as_failure(
                    f"cannot copy {str_src!r} to {str_dest!r}: {e.strerror}")

        return Result.as_success(None)
