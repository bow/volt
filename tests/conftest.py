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
def isolated_project_dir() -> Callable[[Path, str], ACM[Path]]:
    fixture_dir = Path(__file__).parent / "fixtures"

    @contextmanager
    def func(ifs: Path, name: str) -> Generator[Path, None, None]:
        src = fixture_dir / name
        dest = ifs / name
        copytree(src, dest, dirs_exist_ok=False)

        cwd = Path.cwd()
        os.chdir(dest)
        try:
            yield dest
        finally:
            os.chdir(cwd)

    return func
