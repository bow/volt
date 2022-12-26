"""Tests for volt._logging."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

from pytest import CaptureFixture
from structlog import get_logger, reset_defaults
from _pytest.fixtures import SubRequest

from volt.config import _set_exc_style
from volt._logging import init_logging


def test_log_setup(request: SubRequest, capsys: CaptureFixture[str]) -> None:
    def finalizer() -> None:
        reset_defaults()
        _set_exc_style("pretty")

    request.addfinalizer(finalizer)

    init_logging("info")

    log = get_logger("volt")

    def ok() -> None:
        log.info(
            "hello",
            foo="bar",
            attr=True,
            path=Path("/does/not/exist"),
            x="s p a c e d",
            n=5,
        )

    def err() -> None:
        try:
            raise RuntimeError("bzzt")
        except Exception as e:
            log.exception(e)

    ok()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "\x1b[36m\x1b[1m\x1b[7m INF \x1b[0m"
        " \x1b[1mHello\x1b[0m ·"
        "\x1b[90m foo\x1b[0m\x1b[97m=\x1b[0m\x1b[33mbar"
        "\x1b[0m\x1b[90m attr\x1b[0m\x1b[97m=\x1b[0m\x1b[33myes"
        "\x1b[0m\x1b[90m path\x1b[0m\x1b[97m=\x1b[0m\x1b[33m/does/not/exist"
        "\x1b[0m\x1b[90m x\x1b[0m\x1b[97m=\x1b[0m\x1b[33m's p a c e d'"
        "\x1b[0m\x1b[90m n\x1b[0m\x1b[97m=\x1b[0m\x1b[33m5"
        "\x1b[0m"
        "\n"
    )

    _set_exc_style("pretty")
    err()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "bzzt" in captured.err
    assert "def err" in captured.err

    _set_exc_style("plain")
    err()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "bzzt" in captured.err
    assert "def err" not in captured.err
