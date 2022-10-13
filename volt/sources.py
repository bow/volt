"""Site sources."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import cast, Optional

import yaml
from jinja2 import Template
from markdown2 import Markdown
from slugify import slugify
from yaml import SafeLoader

from . import constants
from .config import SiteConfig
from .targets import TemplateTarget


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


class Source(abc.ABC):

    """A source for the site content."""

    # Filesystem path to the source content.
    src: Path

    # Metadata of the content.
    meta: dict


@dataclass(eq=False, frozen=True)
class MarkdownSource(Source):

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

    # Jinja2 template used for rendering content.
    template: Template

    @classmethod
    def from_path(
        cls,
        src: Path,
        template: Template,
        site_config: SiteConfig,
        meta: Optional[dict] = None,
        is_draft: bool = False,
        fm_sep: str = constants.FRONT_MATTER_SEP,
    ) -> "MarkdownSource":
        """Create an instance from a file.

        :param src: Path to the source file.
        :param site_config: Site configuration.
        :param template: Jinja2 template used for rendering the content.
        :param meta: Optional metadata to inject.
        :param fm_sep: String for separating the markdown front matter.

        ."""
        raw_text = src.read_text()
        *top, raw_content = raw_text.split(fm_sep, 2)
        raw_fm = [item for item in top if item]
        fm = {} if not raw_fm else yaml.load(raw_fm[0].strip(), Loader=SafeLoader)

        return cls(
            content=raw_content,
            src=src,
            template=template,
            meta={
                "labels": {},
                "title": None,
                "pub_time": dt.now(),
                "is_draft": is_draft,
                **fm,
                **(meta or {}),
            },
            site_config=site_config,
            is_draft=is_draft,
        )

    @property
    def path_parts(self) -> tuple[str, ...]:
        slug_reps = self.site_config.get("slug_replacements", [])
        num_common_parts = self.site_config.num_common_parts
        url_key = "url"
        parts = (
            [part for part in self.meta[url_key].split("/") if part]
            if self.meta.get(url_key) is not None
            else [f"{slugify(self.meta['title'], replacements=slug_reps)}.html"]
        )
        ps = [*(self.src.parent.parts[num_common_parts:]), *parts]
        if self.is_draft:
            with suppress(IndexError):
                # NOTE: This assumes that the `drafts` folder is located at the same
                #       level as non-draft files.
                del ps[-2]
        return tuple(ps)

    @property
    def rel_url(self) -> str:
        return f"/{'/'.join(self.path_parts)}"

    @cached_property
    def html(self) -> str:
        return cast(str, MD.convert(self.content))

    @property
    def target(self) -> TemplateTarget:
        """Create a :class:`TemplateTarget` instance."""

        render_kwargs = {
            "meta": self.meta,
            "content": self.html,
            "site": self.site_config,
        }

        return TemplateTarget(
            template=self.template,
            render_kwargs=render_kwargs,
            path_parts=self.path_parts,
            src=self.src.relative_to(self.site_config.pwd),
        )
