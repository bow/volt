"""Volt test configurations."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import os
from contextlib import contextmanager, AbstractContextManager as ACM
from pathlib import Path
from shutil import copytree, which
from typing import Callable, Generator

import pytest


@pytest.fixture
def has_git() -> bool:
    return which("git") is not None


@pytest.fixture
def isolated_project_dir() -> dict[str, Callable]:
    fixture_dir = Path(__file__).parent / "fixtures"

    def mk_setup(src: Path) -> Callable[[Path], ACM[Path]]:
        @contextmanager
        def func(ifs: Path) -> Generator[Path, None, None]:
            dest = ifs / src.name
            cwd = Path.cwd()
            copytree(src, dest, dirs_exist_ok=False)
            os.chdir(dest)
            try:
                yield dest
            finally:
                os.chdir(cwd)

        return func

    return {fp.name: mk_setup(fp) for fp in fixture_dir.iterdir() if fp.is_dir()}
