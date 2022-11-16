"""Volt test utilities."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

import yaml
from click.testing import CliRunner


# Layout for test files and directories.
DirLayout = dict[Path | str, str | bytes | Optional["DirLayout"]]


class CommandRunner(CliRunner):
    @contextmanager
    def isolated_filesystem(  # type: ignore[override]
        self,
        layout: Optional[DirLayout] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Generator[Path, None, None]:
        with super().isolated_filesystem(*args, **kwargs) as fs:
            root = Path(fs)
            self._create_files(root, layout)
            yield root

    def _create_files(self, root: Path, layout: Optional[DirLayout]) -> None:

        if layout is None:
            return None

        cur_dir = root
        nodes = [(cur_dir / k, v) for k, v in layout.items()]
        while nodes:
            cur_p, cur_contents = nodes.pop()

            if isinstance(cur_contents, dict):
                cur_p.mkdir(parents=True, exist_ok=True)
                nodes.extend([(cur_p / k, v) for k, v in cur_contents.items()])
                continue

            cur_p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(cur_contents, str):
                cur_p.write_text(cur_contents)
            elif isinstance(cur_contents, bytes):
                cur_p.write_bytes(cur_contents)
            elif cur_contents is None:
                cur_p.touch()

        return None


def assert_dir_empty(path: Path) -> None:
    assert path.is_dir()
    contents = list(path.iterdir())
    assert contents == [], contents


def assert_dir_contains_only(path: Path, fps: list[os.PathLike]) -> None:
    assert path.is_dir()
    contents = sorted(path.iterdir())
    assert contents == sorted([Path(fp) for fp in fps]), contents


def load_config(config_fp: Path) -> dict:
    with config_fp.open() as src:
        config = yaml.safe_load(src)
    return config


def load_project_config(project_dir: Path) -> dict:
    return load_config(project_dir / "volt.yaml")


_sentinel = object()


def has_and_pop(d: dict, key: Any) -> bool:
    try:
        return d.pop(key, _sentinel) is not _sentinel
    except KeyError:
        return False
