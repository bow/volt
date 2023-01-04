"""Static engine."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
from pathlib import Path
from typing import Any, Sequence

import structlog

from .common import Engine
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


def _calc_relpath(target: Path, ref: Path) -> Path:
    """Calculate the target's path relative to the reference.

    :param target: The path to which the relative path will point.
    :param ref: Reference path.

    :returns: The relative path from ``ref`` to ``to``.

    :raises ValueError: when one of the given input paths is not an absolute
        path.

    """
    ref = ref.expanduser()
    target = target.expanduser()
    if not ref.is_absolute() or not target.is_absolute():
        raise ValueError("could not compute relative paths of non-absolute input paths")

    common = Path(os.path.commonpath([ref, target]))
    common_len = len(common.parts)
    ref_uniq = ref.parts[common_len:]
    target_uniq = target.parts[common_len:]

    rel_parts = ("..",) * (len(ref_uniq)) + target_uniq

    return Path(*rel_parts)


def _collect_copy_targets(start_dir: Path, invocation_dir: Path) -> list[CopyTarget]:
    """Gather files from the given start directory recursively as copy targets."""

    src_relpath = _calc_relpath(start_dir, invocation_dir)
    src_rel_len = len(src_relpath.parts)

    targets: list[CopyTarget] = []

    try:
        entries = list(os.scandir(src_relpath))
    except FileNotFoundError:
        return targets
    else:
        while entries:
            de = entries.pop()
            if de.is_dir():
                entries.extend(os.scandir(de))
            else:
                dtoks = Path(de.path).parts[src_rel_len:]
                targets.append(CopyTarget(src=Path(de.path), url_parts=dtoks))

        return targets
