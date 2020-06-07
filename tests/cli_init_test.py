# -*- coding: utf-8 -*-
"""
    Tests for volt init command
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pendulum.tz import local_timezone

from volt.cli import main
from volt.config import CONFIG_FNAME


@pytest.fixture
def fxt_config_tz():
    return {
        "site": {
            "name": None,
            "url": None,
            "timezone": local_timezone().name,
        }
    }


def test_default(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)

        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        assert {f.name for f in wp.iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(CONFIG_FNAME), "r") as src:
            assert yaml.safe_load(src) == fxt_config_tz


def test_custom_dir_no_name(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        pn = "proj"

        assert not wp.joinpath(pn).exists()
        result = runner.invoke(main, ["init", pn])
        assert result.exit_code == 0

        assert {f.name for f in wp.joinpath(pn).iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(pn, CONFIG_FNAME), "r") as src:
            fxt_config_tz["site"]["name"] = "proj"
            assert yaml.safe_load(src) == fxt_config_tz


def test_custom_dir_with_name(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        pn = "proj"
        name = "my_proj"

        assert not wp.joinpath(pn).exists()
        result = runner.invoke(main, ["init", pn, "-n", name])
        assert result.exit_code == 0

        assert {f.name for f in wp.joinpath(pn).iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(pn, CONFIG_FNAME), "r") as src:
            fxt_config_tz["site"]["name"] = name
            assert yaml.safe_load(src) == fxt_config_tz


def test_with_name(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        name = "bzzt"

        result = runner.invoke(main, ["init", "-n", name])
        assert result.exit_code == 0

        assert {f.name for f in wp.iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(CONFIG_FNAME), "r") as src:
            fxt_config_tz["site"]["name"] = name
            assert yaml.safe_load(src) == fxt_config_tz


def test_with_url(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        url = "https://site.com"

        result = runner.invoke(main, ["init", "-u", url])
        assert result.exit_code == 0

        assert {f.name for f in wp.iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(CONFIG_FNAME), "r") as src:
            fxt_config_tz["site"]["url"] = url
            assert yaml.safe_load(src) == fxt_config_tz


def test_with_timezone(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        tz = "Asia/Jakarta"

        result = runner.invoke(main, ["init", "-z", tz])
        assert result.exit_code == 0

        assert {f.name for f in wp.iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME}
        )
        with open(wp.joinpath(CONFIG_FNAME), "r") as src:
            fxt_config_tz["site"]["timezone"] = tz
            assert yaml.safe_load(src) == fxt_config_tz


def test_with_timezone_invalid(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        tz = "Asia/Jakart"

        result = runner.invoke(main, ["init", "-z", tz])
        assert result.exit_code != 0
        assert len(list(wp.iterdir())) == 0


def test_nonwritable_dir(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        os.chmod(fs, 0o555)
        result = runner.invoke(main, ["init"])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        assert "Permission denied" in result.output


def test_nonwritable_custom_dir(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        project_dir = Path(fs).joinpath("foo", "bzzt")
        project_dir.parent.mkdir(parents=True)
        os.chmod(str(project_dir.parent), 0o555)

        result = runner.invoke(main, ["init", str(project_dir)])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        assert "Permission denied" in result.output


def test_nonempty(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        exst_file = wp.joinpath("existing")
        exst_file.write_text("boom")

        result = runner.invoke(main, ["init"])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        # Expected only 1 item: the preexisting file
        assert set(wp.iterdir()) == {exst_file}


def test_nonempty_with_force(fxt_config_tz):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        exst_file = wp.joinpath("existing")
        exst_file.write_text("boom")

        result = runner.invoke(main, ["init", "-f"])
        assert result.exit_code == 0

        assert {f.name for f in wp.iterdir()} == (
            {"contents", "templates", "assets", CONFIG_FNAME, "existing"}
        )
        with open(wp.joinpath(CONFIG_FNAME), "r") as src:
            assert yaml.safe_load(src) == fxt_config_tz
