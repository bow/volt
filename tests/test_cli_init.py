# -*- coding: utf-8 -*-
"""
    Tests for volt init command
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os
from pathlib import Path

import pytest
import toml
import tzlocal
from click.testing import CliRunner

from volt.cli import main
from volt.config import CONFIG_FNAME


@pytest.fixture
def exp_cfg():
    sc = {
        "name": "",
        "url": "",
        "timezone": tzlocal.get_localzone().zone,
    }
    return {"site": sc}


def test_default(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)

        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.iterdir())) == 4
        assert wp.joinpath("contents").exists()
        assert wp.joinpath("templates").exists()
        assert wp.joinpath("static").exists()
        cfg_path = wp.joinpath(CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            assert toml.load(src) == exp_cfg


def test_custom_dir_no_name(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        pn = "proj"

        assert not wp.joinpath(pn).exists()
        result = runner.invoke(main, ["init", pn])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.joinpath(pn).iterdir())) == 4
        assert wp.joinpath(pn, "contents").exists()
        assert wp.joinpath(pn, "templates").exists()
        assert wp.joinpath(pn, "static").exists()
        cfg_path = wp.joinpath(pn, CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            exp_cfg["site"]["name"] = "proj"
            assert toml.load(src) == exp_cfg


def test_custom_dir_with_name(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        pn = "proj"
        name = "my_proj"

        assert not wp.joinpath(pn).exists()
        result = runner.invoke(main, ["init", pn, "-n", name])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.joinpath(pn).iterdir())) == 4
        assert wp.joinpath(pn, "contents").exists()
        assert wp.joinpath(pn, "templates").exists()
        assert wp.joinpath(pn, "static").exists()
        cfg_path = wp.joinpath(pn, CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            exp_cfg["site"]["name"] = name
            assert toml.load(src) == exp_cfg


def test_with_name(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        name = "bzzt"

        result = runner.invoke(main, ["init", "-n", name])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.iterdir())) == 4
        assert wp.joinpath("contents").exists()
        assert wp.joinpath("templates").exists()
        assert wp.joinpath("static").exists()
        cfg_path = wp.joinpath(CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            exp_cfg["site"]["name"] = name
            assert toml.load(src) == exp_cfg


def test_with_url(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        url = "https://site.com"

        result = runner.invoke(main, ["init", "-u", url])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.iterdir())) == 4
        assert wp.joinpath("contents").exists()
        assert wp.joinpath("templates").exists()
        assert wp.joinpath("static").exists()
        cfg_path = wp.joinpath(CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            exp_cfg["site"]["url"] = url
            assert toml.load(src) == exp_cfg


def test_with_timezone(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        tz = "Asia/Jakarta"

        result = runner.invoke(main, ["init", "-z", tz])
        assert result.exit_code == 0
        # Expected 4 items: contents dir, templates dir, static dir, and config
        assert len(list(wp.iterdir())) == 4
        assert wp.joinpath("contents").exists()
        assert wp.joinpath("templates").exists()
        assert wp.joinpath("static").exists()
        cfg_path = wp.joinpath(CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            exp_cfg["site"]["timezone"] = tz
            assert toml.load(src) == exp_cfg


def test_with_timezone_invalid(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        tz = "Asia/Jakart"

        result = runner.invoke(main, ["init", "-z", tz])
        assert result.exit_code != 0
        assert len(list(wp.iterdir())) == 0


def test_nonwritable_dir(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        os.chmod(fs, 0o555)
        result = runner.invoke(main, ["init"])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        assert f"Permission denied" in result.output


def test_nonwritable_custom_dir(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        project_dir = Path(fs).joinpath("foo", "bzzt")
        project_dir.parent.mkdir(parents=True)
        os.chmod(str(project_dir.parent), 0o555)

        result = runner.invoke(main, ["init", str(project_dir)])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        assert f"Permission denied" in result.output


def test_nonempty(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        exst_file = wp.joinpath("existing")
        exst_file.write_text("boom")

        result = runner.invoke(main, ["init"])
        assert result.exit_code != 0
        assert isinstance(result.exception, SystemExit)
        # Expected only 1 item: the preexisting file
        assert list(wp.iterdir()) == [exst_file]


def test_nonempty_with_force(exp_cfg):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        wp = Path(fs)
        exst_file = wp.joinpath("existing")
        exst_file.write_text("boom")

        result = runner.invoke(main, ["init", "-f"])
        assert result.exit_code == 0
        # Expected 5 items: contents dir, templates dir, static dir, config,
        # and the file
        wp_contents = list(wp.iterdir())
        assert len(wp_contents) == 5
        assert exst_file.exists()
        assert wp.joinpath("contents").exists()
        assert wp.joinpath("templates").exists()
        assert wp.joinpath("static").exists()
        cfg_path = wp.joinpath(CONFIG_FNAME)
        assert cfg_path.exists()
        with open(str(cfg_path), "r") as src:
            assert toml.load(src) == exp_cfg
