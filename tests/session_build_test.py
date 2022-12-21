"""Tests for volt.session.build."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from filecmp import cmp
from pathlib import Path
from typing import Callable

import pytest
from structlog.testing import capture_logs

from . import utils as u

from volt import constants, error as err, session
from volt.config import Config


def test_ok_minimal(
    tmp_path: Path,
    isolated_project_dir: Callable,
    project_dirs: dict[str, Path],
) -> None:

    fixture_name = "ok_minimal"

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )

        assert not config.target_dir.exists()

        with capture_logs() as logs:
            assert logs == []
            site = session.build(config=config)
            assert u.log_exists(logs, event="build completed", log_level="info")

        assert site is not None

        target_dir = config.target_dir
        assert target_dir.exists()

        u.assert_dir_contains_only(target_dir, ["assets", "index.html"])
        u.assert_dir_contains_only(target_dir / "assets", ["style.css"])

        project_dir_built = project_dirs[f"{fixture_name}.built"]
        target_dir_built = project_dir_built / "target"

        assert cmp(target_dir / "index.html", target_dir_built / "index.html")
        assert cmp(
            target_dir / "assets/style.css", target_dir_built / "assets/style.css"
        )


def test_ok_extended(
    tmp_path: Path,
    isolated_project_dir: Callable,
    project_dirs: dict[str, Path],
) -> None:

    fixture_name = "ok_extended"

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )

        assert not config.target_dir.exists()

        with capture_logs() as logs:
            assert logs == []
            site = session.build(config=config)
            assert u.log_exists(logs, event="build completed", log_level="info")

        assert site is not None

        target_dir = config.target_dir
        assert target_dir.exists()

        u.assert_dir_contains_only(target_dir, ["assets", "index.html", "foo.html"])
        u.assert_dir_contains_only(target_dir / "assets", ["modified.css"])

        project_dir_built = project_dirs[f"{fixture_name}.built"]
        target_dir_built = project_dir_built / "target"

        assert cmp(target_dir / "index.html", target_dir_built / "index.html")
        assert cmp(target_dir / "foo.html", target_dir_built / "foo.html")
        assert cmp(
            target_dir / "assets/modified.css", target_dir_built / "assets/modified.css"
        )


def test_err_theme_missing(
    tmp_path: Path,
    isolated_project_dir: Callable,
) -> None:

    with isolated_project_dir(tmp_path, "ok_minimal") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._theme_name = "foo"

        assert not config.target_dir.exists()

        with capture_logs() as logs:
            assert logs == []
            with pytest.raises(
                err.VoltConfigError,
                match=f"theme 'foo' not found in {config.themes_dir}",
            ):
                session.build(config=config)
            assert u.log_exists(logs, event="build failed", log_level="error")
            assert not u.log_exists(
                logs,
                event="build failed -- keeping current build",
                log_level="error",
            )

        assert not config.target_dir.exists()


def test_err_theme_missing_with_existing_build(
    tmp_path: Path,
    isolated_project_dir: Callable,
) -> None:

    with isolated_project_dir(tmp_path, "ok_minimal.built") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._theme_name = "foo"

        assert config.target_dir.exists()

        with capture_logs() as logs:
            assert logs == []
            with pytest.raises(
                err.VoltConfigError,
                match=f"theme 'foo' not found in {config.themes_dir}",
            ):
                session.build(config=config)
            assert not u.log_exists(logs, event="build failed", log_level="error")
            assert u.log_exists(
                logs,
                event="build failed -- keeping current build",
                log_level="error",
            )
