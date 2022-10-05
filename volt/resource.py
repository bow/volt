"""Site resource."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
import filecmp
import shutil
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import Optional, Tuple

import yaml
from jinja2 import Template
from markdown2 import Markdown
from slugify import slugify
from yaml import SafeLoader

from . import constants
from . import exceptions as excs
from .config import SiteConfig

__all__ = ["MarkdownContent"]


MD = Markdown(
    extras={
        "fenced-code-blocks": {
            "nowrap": False,
            "full": False,
            "title": "",
            "noclasses": False,
            "classprefix": "",
            "cssclass": "hl",
            "csstyles": "",
            "prestyles": "",
            "cssfile": "",
            "noclobber_cssfile": False,
            "linenos": False,
            "hl_lines": [],
            "linenostart": 1,
            "linenostep": 1,
            "linenospecial": 0,
            "nobackground": False,
            "lineseparator": "\n",
            "lineanchors": "",
            "anchorlinenos": False,
        },
        "markdown-in-html": {},
        "header-ids": {},
    }
)


class Target(abc.ABC):

    """A single file created in the site output directory."""

    # Path parts / tokens to the target.
    path_parts: Tuple[str, ...]

    # Filesystem path to the source of this target.
    src_path: Optional[Path] = field(default=None)

    @abc.abstractmethod
    def write(self, parent_dir: Path) -> None:
        raise NotImplementedError()


@dataclass(frozen=True)
class PageTarget(Target):

    """A single HTML page target."""

    # Raw HTML text content.
    content: str

    # Path parts / tokens to the target.
    path_parts: Tuple[str, ...]

    # Filesystem path to the source of this target.
    src_path: Optional[Path] = field(default=None)

    def write(self, parent_dir: Path) -> None:
        """Write the text content to the destination."""
        try:
            (parent_dir.joinpath(*self.path_parts)).write_text(self.content)
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


class Content(abc.ABC):

    """A source for the site content."""

    # Filesystem path to the source content.
    src: Path

    # Metadata of the content.
    meta: dict


@dataclass(eq=False, frozen=True)
class MarkdownContent(Content):

    """A markdown source of the site content."""

    # Filesystem path to the source content.
    src: Path

    # Metadata of the content.
    meta: dict

    # Markdown text of the content, without any metadata.
    content: str

    # Whether the content is draft or not.
    is_draft: bool

    # Site configuration.
    site_config: SiteConfig

    @classmethod
    def from_path(
        cls,
        src: Path,
        site_config: SiteConfig,
        meta: Optional[dict] = None,
        is_draft: bool = False,
        fm_sep: str = constants.FRONT_MATTER_SEP,
    ) -> "MarkdownContent":
        """Create an instance from a file.

        :param src: Path to the source file.
        :param site_config: Site configuration.
        :param meta: Optional metadata to inject.
        :param fm_sep: String for separating the markdown front matter.

        ."""
        raw_text = src.read_text()
        *top, raw_content = raw_text.split(fm_sep, 2)
        raw_fm = [item for item in top if item]
        fm = {} if not raw_fm else yaml.load(raw_fm[0].strip(), Loader=SafeLoader)

        return cls(
            src=src,
            meta={
                "labels": {},
                "title": None,
                "pub_time": dt.now(),
                "is_draft": is_draft,
                **fm,
                **(meta or {}),
            },
            is_draft=is_draft,
            content=raw_content,
            site_config=site_config,
        )

    @cached_property
    def path_parts(self) -> tuple[str, ...]:
        slug_reps = self.site_config.get("slug_replacements", [])
        num_common_parts = self.site_config.num_common_parts
        parts = (
            [part for part in self.meta["page"].split("/") if part]
            if self.meta.get("page") is not None
            else [f"{slugify(self.meta['title'], replacements=slug_reps)}.html"]
        )
        ps = [*(self.src.parent.parts[num_common_parts:]), *parts]
        if self.is_draft:
            with suppress(IndexError):
                # NOTE: This assumes that the `drafts` folder is located at the same
                #       level as non-draft files.
                del ps[-2]
        return tuple(ps)

    @cached_property
    def rel_url(self) -> str:
        return f"/{'/'.join(self.path_parts)}"

    def to_target(
        self,
        template: Template,
    ) -> PageTarget:
        """Create a :class:`PageTarget` instance from the instance.

        :param template: Jinja2 template to use.

        """
        rendered = template.render(
            meta=self.meta,
            content=MD.convert(self.content),
            site=self.site_config,
        )
        return PageTarget(
            src_path=self.src.relative_to(self.site_config.pwd),
            content=rendered,
            path_parts=self.path_parts,
        )
