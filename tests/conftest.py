"""Volt test configurations."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from shutil import copytree, which
from typing import Callable

import pytest


@pytest.fixture
def has_git() -> bool:
    return which("git") is not None


@pytest.fixture
def project_dirs() -> dict[str, Callable]:
    fixture_dir = Path(__file__).parent / "fixtures"

    def mk_setup(src: Path) -> Callable[[Path], Path]:
        def func(ifs: Path) -> Path:
            dest = ifs / src.name
            copytree(src, dest, dirs_exist_ok=False)
            return dest

        return func

    return {fp.name: mk_setup(fp) for fp in fixture_dir.iterdir() if fp.is_dir()}
