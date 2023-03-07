"""Tests for volt.session.edit."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from volt import constants, error as err, session
from volt.config import Config


def test_ok_drafts_no_create(
    tmp_path: Path,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:

    fixture_name = "ok_extended"
    edit_func = mocker.patch("volt.session.click.edit")

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._with_drafts = True

        draft_fp = config.sources_dir / ".drafts" / "bar.md"

        assert draft_fp.exists()

        session.edit(config, query="bar")

        edit_func.assert_called_once_with(filename=f"{draft_fp}")


def test_ok_drafts_create_match_new(
    tmp_path: Path,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:

    fixture_name = "ok_extended"
    edit_func = mocker.patch("volt.session.click.edit")
    edit_func.return_value = "new-contents"

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._with_drafts = True

        draft_fp = config.sources_dir / ".drafts" / "quux.md"
        assert not draft_fp.exists()

        session.edit(config, query="quux", create=True)

        edit_func.assert_called_once_with(
            text="---\ntitle: Quux\n---",
            extension=".md",
            require_save=False,
        )

        assert draft_fp.exists()
        assert draft_fp.read_text() == "new-contents"


def test_ok_drafts_create_match_existing(
    tmp_path: Path,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:

    fixture_name = "ok_extended"
    edit_func = mocker.patch("volt.session.click.edit")

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._with_drafts = True

        draft_fp = config.sources_dir / ".drafts" / "bar.md"
        assert draft_fp.exists()
        draft_fp_contents = draft_fp.read_text()

        session.edit(config, query="bar", create=False)

        edit_func.assert_called_once_with(filename=f"{draft_fp}")

        assert draft_fp.exists()
        assert draft_fp.read_text() == draft_fp_contents


def test_err_minimal_no_match(
    tmp_path: Path,
    mocker: MockerFixture,
    isolated_project_dir: Callable,
) -> None:

    fixture_name = "ok_extended"
    edit_func = mocker.patch("volt.session.click.edit")

    with isolated_project_dir(tmp_path, fixture_name) as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        config._with_drafts = True

        with pytest.raises(err.VoltCliError, match="found no matching file for 'quux'"):
            session.edit(config, query="quux")

        edit_func.assert_not_called()
