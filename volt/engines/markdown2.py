"""Markdown engine based on markdown2."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime as dt
from functools import cached_property
from pathlib import Path
from typing import cast, Any, Callable, Optional, Self, Sequence
from urllib.parse import urljoin

import pendulum
import yaml
from jinja2 import Template
from markdown2 import Markdown
from pendulum.datetime import DateTime
from slugify import slugify
from yaml import SafeLoader

from .common import Engine
from .. import constants, error as err
from ..config import Config
from ..targets import TemplateTarget


__all__ = ["MarkdownEngine", "MarkdownSource"]


class MarkdownEngine(Engine):

    """Engine that creates HTML targets using the markdown2 library."""

    default_extras = {
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
        "markdown-in-html": True,
        "header-ids": True,
        "footnotes": True,
    }

    @staticmethod
    def make_converter(
        extras: Optional[dict] = None,
        default_extras: dict = default_extras,
    ) -> Callable[[str], str]:
        resolved_extras = _resolve_extras(extras, default_extras)

        kwargs: dict = {}
        if isinstance((fd := resolved_extras.get("footnotes", None)), dict):
            for k in ("footnote_return_symbol", "footnote_title"):
                if (v := fd.get(k)) is not None:
                    kwargs[k] = v

        return cast(
            Callable[[str], str], Markdown(extras=resolved_extras, **kwargs).convert
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        template_name = self.opts.pop("template_name", "page.html.j2")
        try:
            self.template = self.theme.load_template_file(template_name)
        except err.VoltMissingTemplateError:
            default_fp = Path(__file__).parent / "defaults" / f"{template_name}"
            self.template = Template(default_fp.read_text())

        self.extras = self.opts.pop("extras", None)

    def create_targets(self) -> Sequence[TemplateTarget]:

        config = self.config
        get_sources = self.get_sources
        converter = self.make_converter(self.extras)

        fps = get_sources() + (get_sources(drafts=True) if config.with_drafts else [])

        targets = [
            MarkdownSource.from_path(
                src=fp,
                config=config,
                is_draft=is_draft,
                converter=converter,
            ).to_template_target(self.template)
            for fp, is_draft in fps
        ]

        return targets

    def get_sources(self, drafts: bool = False) -> list[tuple[Path, bool]]:
        eff_dir = self.source_dir if not drafts else self.source_drafts_dir
        return [(p, drafts) for p in eff_dir.glob(f"*{constants.MARKDOWN_EXT}")]


@dataclass(kw_only=True, eq=False)
class MarkdownSource:

    """A markdown source parsed using the markdown2 library."""

    # FileSystem path to the source content.
    src: Path

    # Metadata of the content.
    meta: dict

    # Site configuration.
    config: Config

    # Whether the content is draft or not.
    is_draft: bool

    # Markdown text of the body, without any metadata.
    body: str

    # Markdown converter.
    converter: Callable[[str], str]

    @classmethod
    def from_path(
        cls,
        src: Path,
        config: Config,
        converter: Callable[[str], str],
        meta: Optional[dict] = None,
        is_draft: bool = False,
        fm_sep: str = constants.FRONT_MATTER_SEP,
    ) -> Self:
        """Create an instance from a file.

        :param src: Path to the source file.
        :param config: Site configuration.
        :param meta: Optional metadata to inject.
        :param fm_sep: String for separating the markdown front matter.

        ."""
        raw_text = src.read_text()
        *top, raw_body = raw_text.split(fm_sep, 2)
        raw_fm = [item for item in top if item]
        fm = {} if not raw_fm else yaml.load(raw_fm[0].strip(), Loader=SafeLoader)

        return cls(
            body=raw_body,
            src=src,
            # TODO: Validate minimal front matter metadata.
            meta={**fm, **(meta or {})},
            config=config,
            is_draft=is_draft,
            converter=converter,
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
    def url_abs(self) -> str:
        return urljoin(self.config.url, self.url)

    @property
    def title(self) -> str:
        return self.meta.get("title") or self.src.stem

    @cached_property
    def pub_time(self) -> Optional[DateTime]:
        value = self.meta.get("pub_time", None)
        exc = err.VoltResourceError(
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
        return self.converter(self.body)

    def to_template_target(self, template: Template) -> TemplateTarget:
        """Create a :class:`TemplateTarget` instance."""

        return TemplateTarget(
            url=self.url,
            template=template,
            render_kwargs={
                "meta": {**self.meta, "url": self.url},
                "content": self.html,
            },
            src=self.src.relative_to(self.config.project_dir),
        )


def _resolve_extras(extras: Optional[dict], default_extras: dict) -> dict:
    resolved = deepcopy(default_extras)
    extras = extras or {}

    for k, v in extras.items():
        if v is False:
            resolved.pop(k, None)
        else:
            resolved[k] = v

    return resolved
