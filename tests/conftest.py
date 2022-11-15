"""Volt test configurations."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from shutil import which

import pytest


@pytest.fixture
def has_git() -> bool:
    return which("git") is not None
