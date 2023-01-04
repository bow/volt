"""Markdown engine based on markdown2."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing import Any, Sequence

from jinja2 import Template

from .common import Engine
from .. import error as err
from ..constants import MARKDOWN_EXT
from ..sources import Markdown2Source
from ..targets import TemplateTarget


__all__ = ["Markdown2Engine"]


class Markdown2Engine(Engine):

    """Engine that creates HTML targets using the markdown2 library."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        template_name = self.opts.pop("template_name", "page.html.j2")
        try:
            self.template = self.theme.load_template_file(template_name)
        except err.VoltMissingTemplateError:
            default_fp = Path(__file__).parent / "defaults" / f"{template_name}"
            self.template = Template(default_fp.read_text())

    def create_targets(self) -> Sequence[TemplateTarget]:

        config = self.config
        get_sources = self.get_sources

        fps = get_sources() + (get_sources(drafts=True) if config.with_drafts else [])

        targets = [
            Markdown2Source.from_path(
                src=fp, config=config, is_draft=is_draft
            ).to_template_target(self.template)
            for fp, is_draft in fps
        ]

        return targets

    def get_sources(self, drafts: bool = False) -> list[tuple[Path, bool]]:
        eff_dir = self.source_dir if not drafts else self.source_drafts_dir
        return [(p, drafts) for p in eff_dir.glob(f"*{MARKDOWN_EXT}")]
