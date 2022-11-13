"""Volt test configurations."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from shutil import which
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def log_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("volt.cli.init_logging")


@pytest.fixture
def has_git() -> bool:
    return which("git") is not None
