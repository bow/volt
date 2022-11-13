"""Tests for volt.cli."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from unittest.mock import MagicMock

import yaml
from pytest_mock import MockerFixture

from volt import cli

from . import utils as u


def test_new_ok_e2e(log_init: MagicMock, has_git: bool) -> None:
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

        config = u.load_config(ifs / "volt.yaml")
        # Author and language are too env-dependent; enough to check that they exist.
        assert u.has_and_pop(config, "author")
        assert u.has_and_pop(config, "language")
        assert config == {
            "name": "",
            "url": "https://site.net",
            "description": "",
        }

    return None


def test_new_ok_minimal(mocker: MockerFixture, log_init: MagicMock) -> None:
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


def test_new_ok_extended(mocker: MockerFixture, log_init: MagicMock):
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
