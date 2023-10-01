"""Tests for volt.session.build."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from filecmp import cmp
from pathlib import Path
from typing import Callable

import pytest
from pytest_structlog import StructuredLogCapture

from . import utils as u

from volt import constants, error as err, session
from volt.config import Config


def test_ok_minimal(
    tmp_path: Path,
    isolated_project_dir: Callable,
    project_dirs: dict[str, Path],
    log: StructuredLogCapture,
) -> None:

    fixture_name = "ok_minimal"

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )

        assert not config.output_dir.exists()

        site = session.build(config=config)
        assert log.has("build completed", level="info")

        assert site is not None

        output_dir = config.output_dir
        assert output_dir.exists()

        u.assert_dir_contains_only(output_dir, ["assets", "index.html"])
        u.assert_dir_contains_only(output_dir / "assets", ["style.css"])

        project_dir_built = project_dirs[f"{fixture_name}.built"]
        output_dir_built = project_dir_built / "output"

        assert cmp(output_dir / "index.html", output_dir_built / "index.html")
        assert cmp(
            output_dir / "assets/style.css", output_dir_built / "assets/style.css"
        )


def test_ok_extended(
    tmp_path: Path,
    isolated_project_dir: Callable,
    project_dirs: dict[str, Path],
    log: StructuredLogCapture,
) -> None:

    fixture_name = "ok_extended"

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._with_draft = False

        assert not config.output_dir.exists()

        site = session.build(config=config)
        assert log.has("build completed", level="info")

        assert site is not None

        output_dir = config.output_dir
        assert output_dir.exists()

        u.assert_dir_contains_only(
            output_dir, ["assets", "gallery", "index.html", "foo.html"]
        )
        u.assert_dir_contains_only(output_dir / "assets", ["imgs", "modified.css"])

        project_dir_built = project_dirs[f"{fixture_name}.built"]
        output_dir_built = project_dir_built / "output"

        assert cmp(output_dir / "index.html", output_dir_built / "index.html")
        assert cmp(output_dir / "foo.html", output_dir_built / "foo.html")
        assert cmp(
            output_dir / "assets/modified.css", output_dir_built / "assets/modified.css"
        )


def test_err_theme_missing(
    tmp_path: Path,
    isolated_project_dir: Callable,
    log: StructuredLogCapture,
) -> None:

    with isolated_project_dir(tmp_path, "ok_minimal") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._theme_name = "foo"

        assert not config.output_dir.exists()

        with pytest.raises(
            err.VoltConfigError,
            match=f"theme 'foo' not found in {config.themes_dir}",
        ):
            session.build(config=config)

        assert log.has("build failed", level="error")
        assert not log.has("build failed -- keeping current build", level="error")

        assert not config.output_dir.exists()


def test_err_theme_missing_with_existing_build(
    tmp_path: Path,
    isolated_project_dir: Callable,
    log: StructuredLogCapture,
) -> None:

    with isolated_project_dir(tmp_path, "ok_minimal.built") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._theme_name = "foo"

        assert config.output_dir.exists()

        with pytest.raises(
            err.VoltConfigError,
            match=f"theme 'foo' not found in {config.themes_dir}",
        ):
            session.build(config=config)

        assert not log.has("build failed", level="error")
        assert log.has("build failed -- keeping current build", level="error")
