"""Static engine."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing import Any, Sequence

import structlog

from .common import Engine, _collect_copy_targets
from .. import error as err
from ..constants import STATIC_DIR_NAME
from ..targets import CopyTarget


__all__ = ["StaticEngine"]


log = structlog.get_logger(__name__)


class StaticEngine(Engine):

    """Engine that resolves and copies static files."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if (kwargs.get("source_dir_name") or STATIC_DIR_NAME) != STATIC_DIR_NAME:
            raise err.VoltConfigError(
                f"if specified, 'source' must be {STATIC_DIR_NAME!r} for {self.name}"
            )
        kwargs["source_dir_name"] = STATIC_DIR_NAME
        super().__init__(*args, **kwargs)

    @property
    def source_drafts_dir(self) -> Path:
        log.warn(f"drafts directory is not applicable to {self.name}")
        return self.source_dir

    def create_targets(self) -> Sequence[CopyTarget]:
        config = self.config
        theme = self.theme

        targets = {
            target.url: target
            for target in _collect_copy_targets(theme.static_dir, config.invoc_dir)
        }

        for user_target in _collect_copy_targets(config.static_dir, config.invoc_dir):
            url = user_target.url
            if url in targets:
                log.warn("using user-defined target instead of theme target", url=url)
            targets[url] = user_target

        return list(targets.values())
