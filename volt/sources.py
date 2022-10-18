"""Site sources."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import cast, Optional
from urllib.parse import urljoin

import pendulum
import yaml
from jinja2 import Template
from markdown2 import Markdown
from pendulum.datetime import DateTime
from slugify import slugify
from yaml import SafeLoader

from . import constants
from .exceptions import VoltResourceError
from .config import Config
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
    config: Config

    # Jinja2 template used for rendering content.
    template: Template

    @classmethod
    def from_path(
        cls,
        src: Path,
        template: Template,
        config: Config,
        meta: Optional[dict] = None,
        is_draft: bool = False,
        fm_sep: str = constants.FRONT_MATTER_SEP,
    ) -> "MarkdownSource":
        """Create an instance from a file.

        :param src: Path to the source file.
        :param config: Site configuration.
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
            # TODO: Validate minimal front matter metadata.
            meta={
                "labels": {},
                "title": None,
                "is_draft": is_draft,
                **fm,
                **(meta or {}),
            },
            config=config,
            is_draft=is_draft,
        )

    @cached_property
    def url(self) -> str:
        config = self.config
        url_key = "url"
        parts = (
            [part for part in self.meta[url_key].split("/") if part]
            if self.meta.get(url_key) is not None
            else [f"{slugify(self.title, replacements=config.slug_replacements)}.html"]
        )
        ps = [*(self.src.parent.parts[config.num_common_parts :]), *parts]
        if self.is_draft:
            with suppress(IndexError):
                # NOTE: This assumes that the `drafts` folder is located at the same
                #       level as non-draft files.
                del ps[-2]

        return f"/{'/'.join(ps)}"

    @property
    def abs_url(self) -> str:
        return urljoin(self.config.url, self.url)

    @property
    def title(self) -> str:
        return cast(str, self.meta["title"])

    @cached_property
    def pub_time(self) -> Optional[DateTime]:
        value = self.meta.get("pub_time", None)
        exc = VoltResourceError(
            f"value {value!r} in {str(self.src)!r} is not a valid datetime"
        )
        if value is None:
            return value
        if isinstance(value, str):
            rv = pendulum.parse(value)
            if isinstance(rv, DateTime):
                return rv
            raise exc
        if isinstance(value, dt):
            return pendulum.instance(value)
        raise exc

    @cached_property
    def html(self) -> str:
        return cast(str, MD.convert(self.content))

    @property
    def target(self) -> TemplateTarget:
        """Create a :class:`TemplateTarget` instance."""

        render_kwargs = {
            "meta": self.meta,
            "content": self.html,
            "config": self.config,
        }

        return TemplateTarget(
            url=self.url,
            template=self.template,
            render_kwargs=render_kwargs,
            src=self.src.relative_to(self.config.project_dir),
        )
