"""Tests for volt.session.new."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Callable, Optional

import pytest
from pytest_mock import MockerFixture
from structlog.testing import capture_logs

from . import utils as u

from volt import session, error as err


def test_ok_minimal(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    project_dir = session.new(
        dir_name=None,
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme=None,
        vcs=None,
    )

    assert project_dir == tmp_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "",
        "url": "",
        "description": "",
    }

    return None


def test_err_not_empty_no_force(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    config_fp = tmp_path / "volt.toml"
    config_fp.write_text("existing")

    with pytest.raises(
        err.VoltCliError,
        match=f"project directory {tmp_path} contains files",
    ):
        session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs=None,
        )

    u.assert_dir_contains_only(tmp_path, [config_fp])
    assert config_fp.read_text() == "existing"

    return None


def test_ok_project_path_abs_conflict(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    dir_path = tmp_path.resolve() / "foo" / "bar"

    with capture_logs() as logs:
        assert logs == []
        project_dir = session.new(
            dir_name=f"{dir_path}",
            invoc_dir=tmp_path,
            project_dir=tmp_path.resolve() / "bzzt",
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs=None,
        )
        assert u.log_exists(
            logs,
            event=(
                "ignoring specified project path as command is invoked with an absolute"
                " path"
            ),
            log_level="warning",
        )

    assert project_dir == dir_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "Bar",
        "url": "",
        "description": "",
    }

    return None


def test_ok_no_theme(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    project_dir = session.new(
        dir_name="foo/bar",
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme="ion",
        vcs=None,
    )

    assert project_dir == tmp_path / "foo" / "bar"

    assert_new_project_layout(project_dir, with_git=False, theme="ion")

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site", "theme"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "Bar",
        "url": "",
        "description": "",
    }

    theme_config = config["theme"]
    assert theme_config == {"name": "ion"}

    return None


def test_ok_inferred_name(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    project_dir = session.new(
        dir_name="foo/bar",
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme=None,
        vcs=None,
    )

    assert project_dir == tmp_path / "foo" / "bar"

    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "Bar",
        "url": "",
        "description": "",
    }

    return None


def test_ok_infer_author_no_git(tmp_path: Path, mocker: MockerFixture) -> None:
    u.assert_dir_empty(tmp_path)

    which_m = mocker.patch("volt.session.which")
    which_m.return_value = None

    project_dir = session.new(
        dir_name=None,
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme=None,
        vcs=None,
    )

    assert project_dir == tmp_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "",
        "url": "",
        "description": "",
    }

    which_m.assert_called_once()

    return None


def test_ok_infer_author_no_git_user_name(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    u.assert_dir_empty(tmp_path)

    which_m = mocker.patch("volt.session.which")
    git_exe = "/path/to/git"
    which_m.return_value = git_exe

    run_m = mocker.patch("volt.session.sp.run")
    cmd_toks = [git_exe, "config", "--get", "user.name"]
    run_m.side_effect = func_failed_process_for(cmd_toks)

    with capture_logs() as logs:
        assert logs == []
        project_dir = session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs=None,
        )
        run_m.assert_called_once_with(cmd_toks, capture_output=True)
        assert u.log_exists(
            logs,
            event="no author can be inferred as git returns no 'user.name' value",
            log_level="warning",
        )

    assert project_dir == tmp_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    site_config.pop("language", None)
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "",
        "url": "",
        "description": "",
    }

    return None


def test_ok_git_exe_missing(tmp_path: Path, mocker: MockerFixture) -> None:
    u.assert_dir_empty(tmp_path)

    which_m = mocker.patch("volt.session.which")
    which_m.return_value = None

    with capture_logs() as logs:
        assert logs == []
        project_dir = session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs="git",
        )
        assert u.log_exists(
            logs,
            event="can not find git executable",
            log_level="warning",
        )

    assert_new_project_layout(project_dir, with_git=True)

    return None


def test_ok_git_init_fail(tmp_path: Path, mocker: MockerFixture) -> None:
    u.assert_dir_empty(tmp_path)

    which_m = mocker.patch("volt.session.which")
    git_exe = "/path/to/git"
    which_m.return_value = git_exe

    run_m = mocker.patch("volt.session.sp.run")
    cmd_toks = [git_exe, "-C", f"{tmp_path.resolve()}", "init"]
    run_m.side_effect = func_failed_process_for(cmd_toks)

    with capture_logs() as logs:
        assert logs == []
        project_dir = session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs="git",
        )
        run_m.assert_any_call(cmd_toks, capture_output=True)
        assert u.log_exists(logs, event="git init failed", log_level="warning")

    assert_new_project_layout(project_dir, with_git=True)

    return None


def test_ok_git_add_fail(tmp_path: Path, mocker: MockerFixture) -> None:
    u.assert_dir_empty(tmp_path)

    which_m = mocker.patch("volt.session.which")
    git_exe = "/path/to/git"
    which_m.return_value = git_exe

    run_m = mocker.patch("volt.session.sp.run")
    cmd_toks = [git_exe, "-C", f"{tmp_path.resolve()}", "add", "."]
    run_m.side_effect = func_failed_process_for(cmd_toks)

    with capture_logs() as logs:
        assert logs == []
        project_dir = session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs="git",
        )
        run_m.assert_any_call(cmd_toks, capture_output=True)
        assert u.log_exists(logs, event="git add failed", log_level="warning")

    assert_new_project_layout(project_dir, with_git=True)

    return None


def test_err_unsupported_vcs(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    with pytest.raises(ValueError, match="vcs 'subversion' is unsupported"):
        session.new(
            dir_name=None,
            invoc_dir=tmp_path,
            project_dir=tmp_path,
            name="",
            url="",
            authors=[],
            description="",
            language=None,
            force=False,
            theme=None,
            vcs="subversion",  # type: ignore[arg-type]
        )

    assert_new_project_layout(tmp_path, with_git=False)

    return None


def test_ok_infer_lang(tmp_path: Path, mocker: MockerFixture) -> None:
    u.assert_dir_empty(tmp_path)

    locale_m = mocker.patch("volt.session.getlocale")
    locale_m.return_value = ("en_US", "UTF-8")

    project_dir = session.new(
        dir_name=None,
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme=None,
        vcs=None,
    )

    assert project_dir == tmp_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    assert u.has_and_pop(site_config, "authors")
    assert site_config == {
        "name": "",
        "url": "",
        "description": "",
        "language": "en",
    }

    return None


@pytest.mark.parametrize("getlocale_rv", [(None, "???"), ("???", "???")])
def test_ok_infer_lang_missing(
    tmp_path: Path,
    mocker: MockerFixture,
    getlocale_rv: Optional[tuple],
) -> None:
    u.assert_dir_empty(tmp_path)

    locale_m = mocker.patch("volt.session.getlocale")
    locale_m.return_value = getlocale_rv

    project_dir = session.new(
        dir_name=None,
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        authors=[],
        description="",
        language=None,
        force=False,
        theme=None,
        vcs=None,
    )

    assert project_dir == tmp_path
    assert_new_project_layout(project_dir, with_git=False)

    config = u.load_project_config(project_dir)
    u.assert_keys_only(config, ["site"])

    site_config = config["site"]
    assert u.has_and_pop(site_config, "authors")
    assert "language" not in site_config
    assert site_config == {
        "name": "",
        "url": "",
        "description": "",
    }

    return None


def assert_new_project_layout(
    project_dir: Path,
    with_git: bool = True,
    theme: Optional[str] = None,
) -> None:

    theme_dir = project_dir / "theme"
    sources_dir = project_dir / "source"
    config_fp = project_dir / "volt.toml"

    dir_contents = [theme_dir, sources_dir, config_fp]

    if with_git:
        gitignore = project_dir / ".gitignore"
        dir_contents.append(gitignore)

    u.assert_dir_contains_only(project_dir, dir_contents)

    if theme is not None:
        u.assert_dir_contains_only(theme_dir, [theme])
        u.assert_dir_contains_only(sources_dir, ["index.md", "static"])
    else:
        u.assert_dir_empty(theme_dir)
        u.assert_dir_contains_only(sources_dir, ["static"])
        u.assert_dir_empty(sources_dir / "static")


def func_failed_process_for(cmd_toks: list[str]) -> Callable:
    def func(*args: Any, **kwargs: Any) -> CompletedProcess:
        toks = args[0]
        if toks == cmd_toks:
            return CompletedProcess(toks, returncode=1, stdout=b"", stderr=b"")
        return CompletedProcess(toks, returncode=0, stdout=b"", stderr=b"")

    return func
