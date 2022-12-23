"""Tests for volt.cli."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import time
import subprocess as sp
from pathlib import Path
from threading import Thread
from typing import Callable, Optional
from unittest.mock import MagicMock

import pytest
import requests
from pytest_mock import MockerFixture
from requests.exceptions import ConnectionError

from volt import cli, constants
from volt.config import Config

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
        assert res.exit_code == 0, res.output

        u.assert_dir_contains_only(
            ifs,
            [
                *([".gitignore", ".git"] if has_git else []),
                "volt.toml",
                "theme",
                "source",
            ],
        )

        config = u.load_project_config(ifs)
        u.assert_keys_only(config, ["site", "theme"])

        site_config = config["site"]
        site_config.pop("language", None)
        assert u.has_and_pop(site_config, "authors")
        assert site_config == {
            "name": "",
            "url": "https://site.net",
            "description": "",
        }

        theme_config = config["theme"]
        assert theme_config == {"name": "ion"}

        if has_git:
            proc = sp.run(
                ["git", "-C", f"{ifs.resolve()}", "status", "--porcelain"],
                capture_output=True,
            )
            if proc.returncode != 0:
                return None
            stdout_lines = proc.stdout.decode("utf-8").split("\n")
            assert sorted(stdout_lines) == [
                "",
                *[
                    f"A  {fn}"
                    for fn in (
                        ".gitignore",
                        "source/index.md",
                        "theme/ion/static/assets/style.css",
                        "theme/ion/templates/base.html.j2",
                        "theme/ion/templates/page.html.j2",
                        "theme/ion/theme.toml",
                        "volt.toml",
                    )
                ],
            ]

    return None


def test_new_ok_minimal(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.new")
    toks = ["new"]

    with runner.isolated_filesystem() as ifs:

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            dir_name=None,
            invoc_dir=ifs,
            project_dir=ifs,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme="ion",
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
        "--author",
        "Jane Roe",
        "--force",
        "--no-theme",
        "--vcs",
        "none",
        "custom_path",
    ]
    with runner.isolated_filesystem() as ifs:

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            dir_name="custom_path",
            invoc_dir=ifs,
            project_dir=ifs / "custom_project",
            name="custom_name",
            url="",
            authors=["John Doe", "Jane Roe"],
            description="",
            language=None,
            force=True,
            theme=None,
            vcs=None,
        )


def test_build_ok_e2e(isolated_project_dir: Callable) -> None:
    runner = u.CommandRunner()
    toks = ["build"]

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_minimal") as project_dir:

            target_dir = project_dir / constants.PROJECT_TARGET_DIR_NAME
            assert not target_dir.exists()

            res = runner.invoke(cli.root, toks)
            assert res.exit_code == 0, res.output
            assert "build completed" in res.output

            assert target_dir.exists()
            u.assert_dir_contains_only(target_dir, ["assets", "index.html"])
            u.assert_dir_contains_only(target_dir / "assets", ["style.css"])

    return None


def test_build_err_not_project(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.build")
    toks = ["build"]

    with runner.isolated_filesystem() as ifs:

        u.assert_dir_empty(ifs)

        res = runner.invoke(cli.root, toks)
        assert res.exit_code != 0, res.output
        assert "command 'build' works only within a Volt project"

        u.assert_dir_empty(ifs)

        sess_func.assert_not_called()


def test_build_ok_minimal(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.build")
    toks = ["build"]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=ifs, project_dir=ifs),
            clean=True,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == ifs
        assert not config.with_drafts


def test_build_ok_extended(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.build")
    toks = ["-D", "the_project", "build", "--drafts"]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs / "the_project"
        project_dir.mkdir(parents=True, exist_ok=False)

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=project_dir, project_dir=project_dir),
            clean=True,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == project_dir
        assert config.with_drafts


def test_serve_ok_e2e(isolated_project_dir: Callable) -> None:

    host = "127.0.0.1"
    port = u.find_free_port()
    url = f"http://{host}:{port}"
    index_html: Optional[Path] = None

    def serve() -> None:
        runner = u.CommandRunner()
        toks = ["serve", "-h", host, "-p", f"{port}", "--no-sig-handlers"]

        with runner.isolated_filesystem() as ifs:

            with isolated_project_dir(ifs, "ok_extended") as project_dir:

                target_dir = project_dir / constants.PROJECT_TARGET_DIR_NAME
                assert not target_dir.exists()

                nonlocal index_html
                index_html = target_dir / "index.html"

                runner.invoke(cli.root, toks)

    with pytest.raises(ConnectionError, match="Connection refused"):
        requests.get(url, timeout=3)

    thread = Thread(target=serve)
    thread.daemon = True
    thread.start()

    max_wait_secs = 5.0
    wait_duration_secs = 0.2
    waited = 0.0
    while index_html is None or not index_html.exists():
        time.sleep(wait_duration_secs)
        waited += wait_duration_secs
        if waited > max_wait_secs:
            pytest.fail(f"expected build result file {index_html} missing")

    r = requests.get(url, timeout=3)

    assert r.status_code == 200
    assert "<title>ok_extended</title>" in r.text

    return None


def test_serve_ok_minimal(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.serve")
    toks = ["serve"]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=ifs, project_dir=ifs),
            host=None,
            port=5050,
            rebuild=True,
            pre_build=True,
            build_clean=True,
            log_level="info",
            with_sig_handlers=True,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == ifs
        assert config.with_drafts


def test_serve_ok_extended(mocker: MockerFixture) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.serve")
    toks = [
        "serve",
        "-h",
        "0.0.0.0",
        "-p",
        "7070",
        "--no-drafts",
        "--no-pre-build",
        "-q",
    ]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=ifs, project_dir=ifs),
            host="0.0.0.0",
            port=7070,
            rebuild=True,
            pre_build=False,
            build_clean=True,
            log_level="info",
            with_sig_handlers=True,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == ifs
        assert not config.with_drafts
