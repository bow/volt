"""Tests for volt.cli."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import subprocess as sp
from typing import Callable

import pytest
import requests
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from requests.exceptions import ConnectionError

from volt import cli, constants
from volt.config import Config
from volt.error import VoltResourceError

from . import utils as u


def test_new_ok_e2e(log: StructuredLogCapture, has_git: bool) -> None:
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


def test_new_ok_minimal(log: StructuredLogCapture, mocker: MockerFixture) -> None:
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


def test_new_ok_extended(log: StructuredLogCapture, mocker: MockerFixture):
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


def test_build_ok_e2e(
    log: StructuredLogCapture, isolated_project_dir: Callable
) -> None:
    runner = u.CommandRunner()
    toks = ["build"]

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_minimal") as project_dir:

            target_dir = project_dir / constants.PROJECT_TARGET_DIR_NAME
            assert not target_dir.exists()

            res = runner.invoke(cli.root, toks)
            assert res.exit_code == 0, res.output

            assert target_dir.exists()
            u.assert_dir_contains_only(target_dir, ["assets", "index.html"])
            u.assert_dir_contains_only(target_dir / "assets", ["style.css"])

    return None


def test_build_err_not_project(
    log: StructuredLogCapture, mocker: MockerFixture
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.build")
    toks = ["build"]

    with runner.isolated_filesystem() as ifs:

        u.assert_dir_empty(ifs)

        res = runner.invoke(cli.root, toks)
        assert res.exit_code != 0, res.output
        assert log.has(
            "command 'build' works only within a Volt project", level="error"
        )

        u.assert_dir_empty(ifs)

        sess_func.assert_not_called()


@pytest.mark.parametrize("toks", [["build"], ["b"]])
def test_build_ok_minimal(
    log: StructuredLogCapture, mocker: MockerFixture, toks: list[str]
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.build")

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


def test_build_ok_extended(log: StructuredLogCapture, mocker: MockerFixture) -> None:
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


def test_serve_ok_e2e(
    log: StructuredLogCapture, isolated_project_dir: Callable
) -> None:

    host = "127.0.0.1"
    port = u.find_free_port()
    url = f"http://{host}:{port}"
    timeout = 3

    with pytest.raises(ConnectionError, match="Connection refused"):
        requests.get(url, timeout=timeout)

    u.invoke_isolated_server(
        isolated_project_dir,
        project_fixture_name="ok_extended",
        host=host,
        port=port,
        startup_timeout=5.0,
    )

    r = requests.get(url, timeout=timeout)
    assert r.status_code == 200
    assert "<title>ok_extended</title>" in r.text

    return None


def test_serve_ok_minimal(log: StructuredLogCapture, mocker: MockerFixture) -> None:
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


def test_serve_ok_extended(log: StructuredLogCapture, mocker: MockerFixture) -> None:
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


def test_serve_drafts_ok_e2e(
    log: StructuredLogCapture, isolated_project_dir: Callable
) -> None:

    host = "127.0.0.1"
    port = u.find_free_port()
    url = f"http://{host}:{port}"
    req_timeout = 3

    project_dir = u.invoke_isolated_server(
        isolated_project_dir,
        project_fixture_name="ok_extended",
        args=["serve", "-h", host, "-p", f"{port}", "--no-sig-handlers", "--no-drafts"],
        host=host,
        port=port,
        startup_timeout=5.0,
    )

    r_foo = requests.get(f"{url}/foo.html", timeout=req_timeout)
    assert r_foo.status_code == 200
    r_bar = requests.get(f"{url}/bar.html", timeout=req_timeout)
    assert r_bar.status_code == 404

    runner = u.CommandRunner()
    toks = ["-D", f"{project_dir}", "serve", "drafts"]
    runner.invoke(cli.root, toks)

    fp = project_dir / constants.PROJECT_TARGET_DIR_NAME / "bar.html"
    assert u.wait_until_exists(fp)

    r_foo = requests.get(f"{url}/foo.html", timeout=req_timeout)
    assert r_foo.status_code == 200
    r_bar = requests.get(f"{url}/bar.html", timeout=req_timeout)
    assert r_bar.status_code == 200
    assert "<p>This is bar! It's still in draft.</p>" in r_bar.text

    return None


def test_serve_drafts_ok_minimal(
    log: StructuredLogCapture, mocker: MockerFixture
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.serve_drafts")
    toks = ["serve", "drafts"]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=ifs, project_dir=ifs),
            value=None,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == ifs
        assert not config.with_drafts


def test_serve_drafts_ok_extended(
    log: StructuredLogCapture, mocker: MockerFixture
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.serve_drafts")
    toks = ["serve", "drafts", "-s"]

    with runner.isolated_filesystem() as ifs:

        project_dir = ifs

        (project_dir / constants.CONFIG_FILE_NAME).touch()

        res = runner.invoke(cli.root, toks)
        assert res.exit_code == 0, res.output

        sess_func.assert_called_once_with(
            config=Config(invoc_dir=ifs, project_dir=ifs),
            value=True,
        )
        config = sess_func.call_args.kwargs["config"]
        assert config.invoc_dir == ifs
        assert config.project_dir == ifs
        assert not config.with_drafts


def test_edit_ok_e2e(
    log: StructuredLogCapture, mocker: MockerFixture, isolated_project_dir: Callable
) -> None:

    runner = u.CommandRunner()
    edit_func = mocker.patch("volt.session.click.edit")
    edit_func.return_value = "edited-contents"
    toks = ["edit", "--create", "articles", "-n", "quux"]

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_extended") as project_dir:

            edit_target = project_dir / "source" / "articles" / ".drafts" / "quux.md"
            assert not edit_target.exists()

            res = runner.invoke(cli.root, toks)
            assert res.exit_code == 0, res.output

            edit_func.assert_called_once_with(
                text="---\ntitle: Quux\n---",
                extension=".md",
                require_save=False,
            )

            assert edit_target.exists()
            assert edit_target.read_text() == "edited-contents"

    return None


def test_edit_ok_minimal(
    log: StructuredLogCapture,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.edit")
    toks = ["edit", "-n", "foo"]

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_extended") as project_dir:

            res = runner.invoke(cli.root, toks)
            assert res.exit_code == 0, res.output

            sess_func.assert_called_once_with(
                config=Config(invoc_dir=project_dir, project_dir=project_dir),
                query="foo",
                create=None,
                title=None,
            )
            config = sess_func.call_args.kwargs["config"]
            assert config.invoc_dir == project_dir
            assert config.project_dir == project_dir
            assert config.with_drafts

    return None


def test_edit_ok_extended(
    log: StructuredLogCapture,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:
    runner = u.CommandRunner()
    sess_func = mocker.patch("volt.cli.session.edit")
    toks = ["edit", "--published", "--create", "-n", "foo"]

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_extended") as project_dir:

            res = runner.invoke(cli.root, toks)
            assert res.exit_code == 0, res.output

            sess_func.assert_called_once_with(
                config=Config(invoc_dir=project_dir, project_dir=project_dir),
                query="foo",
                create="",
                title=None,
            )
            config = sess_func.call_args.kwargs["config"]
            assert config.invoc_dir == project_dir
            assert config.project_dir == project_dir
            assert not config.with_drafts

    return None


def test_help_with_xcmd(
    log: StructuredLogCapture, isolated_project_dir: Callable
) -> None:
    runner = u.CommandRunner()

    with runner.isolated_filesystem() as ifs:

        with isolated_project_dir(ifs, "ok_extended") as project_dir:

            assert (project_dir / "extension" / "cli.py").exists()

            res0 = runner.invoke(cli.root, [])
            assert res0.exit_code == 0, res0.output
            assert " xcmd " in res0.output, res0.output

            res1 = runner.invoke(cli.root, ["xcmd"])
            assert res1.exit_code == 0, res1.output
            assert " hello-ext " in res1.output, res1.output

            res2 = runner.invoke(cli.root, ["xcmd", "hello-ext"])
            assert res2.exit_code == 0, res2.output
            assert "FooBar!" in res2.output, res2.output
