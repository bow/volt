"""Tests for volt.cli."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import subprocess as sp
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from volt import cli

from . import utils as u


@pytest.fixture(autouse=True)
def log_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("volt.cli.init_logging")


def test_new_ok_e2e(has_git: bool) -> None:
    runner = u.CommandRunner()
    toks = ["new", "-u", "https://site.net"]

    with runner.isolated_filesystem() as ifs:

        u.assert_dir_empty(ifs)

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0

        u.assert_dir_contains_only(
            ifs,
            [
                ifs / fn
                for fn in (
                    *([".gitignore", ".git"] if has_git else []),
                    "volt.yaml",
                    "theme",
                    "source",
                )
            ],
        )

        config = u.load_project_config(ifs)
        config.pop("language", None)
        assert u.has_and_pop(config, "author")
        assert config == {
            "name": "",
            "url": "https://site.net",
            "description": "",
        }

        if has_git:
            proc = sp.run(
                ["git", "-C", f"{ifs.resolve()}", "status", "--porcelain"],
                capture_output=True,
            )
            if proc.returncode != 0:
                return None
            stdout_lines = proc.stdout.decode("utf-8").split("\n")
            assert sorted(stdout_lines) == ["", "A  .gitignore", "A  volt.yaml"]

    return None


def test_new_ok_minimal(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.new")
    toks = ["new"]

    with runner.isolated_filesystem() as ifs:

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0

        sess_func.assert_called_once_with(
            dirname=None,
            invoc_dir=ifs,
            project_dir=ifs,
            name="",
            url="",
            author=None,
            description="",
            language=None,
            force=False,
            vcs="git",
        )


def test_new_ok_extended(mocker: MockerFixture):
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.new")
    toks = [
        "-D",
        "custom_project",
        "new",
        "-n",
        "custom_name",
        "--author",
        "John Doe",
        "--force",
        "--vcs",
        "none",
        "custom_path",
    ]
    with runner.isolated_filesystem() as ifs:

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0

        sess_func.assert_called_once_with(
            dirname="custom_path",
            invoc_dir=ifs,
            project_dir=ifs / "custom_project",
            name="custom_name",
            url="",
            author="John Doe",
            description="",
            language=None,
            force=True,
            vcs=None,
        )
