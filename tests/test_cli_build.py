# -*- coding: utf-8 -*-
"""
    Tests for volt build command
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

import pytest
import toml
from click.testing import CliRunner

from volt.cli import main
from volt.config import CONFIG_FNAME


@pytest.fixture
def fxt_config():
    return {
        "site": {
            "name": "test",
            "url": "http://test.net",
            "timezone": "Europe/Amsterdam"
        }
    }


@pytest.fixture
def fxt_layoutf():
    def f(config):
        return {
            "dirs": ["contents", "assets", "templates"],
            "files": {
                CONFIG_FNAME: toml.dumps(config),
                "templates/page.html": "{{ unit.raw_text }}",
                "contents/foo.md": "---\ntitle: Foo\n---\n\nfoobar",
                "assets/foo1.txt": "this is foo1",
                "assets/txts/bar1.txt": "another file",
            }
        }
    return f


def create_project_fixture(fs, layout):
    for dname in layout["dirs"]:
        fs.joinpath(dname).mkdir()
    for fname, contents in layout["files"].items():
        fp = fs.joinpath(fname)
        fp.parent.mkdir(parents=True, exist_ok=True)
        with fp.open(mode="w") as fh:
            fh.write(contents)


def test_ok(fxt_config, fxt_layoutf):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        fs = Path(fs)

        create_project_fixture(fs, fxt_layoutf(fxt_config))

        result = runner.invoke(main, ["build"])
        assert result.exit_code == 0

        assert {f.name for f in fs.iterdir()} == \
            {"assets", "contents", "templates", "site", "Volt.toml"}

        page = fs.joinpath("site", "foo.html")
        assert page.exists()
        assert page.read_text().strip() == "foobar"

        for asset in ("foo1.txt", "txts/bar1.txt"):
            assert fs.joinpath("site", asset).exists()


def test_ok_no_clean(fxt_config, fxt_layoutf):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        fs = Path(fs)

        create_project_fixture(fs, fxt_layoutf(fxt_config))
        fs.joinpath("site").mkdir()
        fs.joinpath("site", "bzzt").write_text("bzzt")

        result = runner.invoke(main, ["build", "--no-clean"])
        assert result.exit_code == 0

        assert {f.name for f in fs.iterdir()} == \
            {"assets", "contents", "templates", "site", "Volt.toml"}

        page = fs.joinpath("site", "foo.html")
        assert page.exists()
        assert page.read_text().strip() == "foobar"

        for asset in ("foo1.txt", "txts/bar1.txt", "bzzt"):
            assert fs.joinpath("site", asset).exists()


def test_fail_find_pwd(fxt_config, fxt_layoutf):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        fs = Path(fs)

        layout = fxt_layoutf(fxt_config)
        layout["files"].pop(CONFIG_FNAME)
        create_project_fixture(fs, layout)

        result = runner.invoke(main, ["build"])
        assert result.exit_code != 0
        assert "failed to find project directory" in result.output

        assert {f.name for f in fs.iterdir()} == \
            {"assets", "contents", "templates"}


def test_fail_config_load(fxt_config, fxt_layoutf):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        fs = Path(fs)

        layout = fxt_layoutf(fxt_config)
        layout["files"][CONFIG_FNAME] = "foo"
        create_project_fixture(fs, layout)

        result = runner.invoke(main, ["build"])
        assert result.exit_code != 0
        assert "cannot find site configuration in config file" in result.output

        assert {f.name for f in fs.iterdir()} == \
            {"assets", "contents", "templates", "Volt.toml"}


def test_fail_build_template_load(fxt_config, fxt_layoutf):
    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        fs = Path(fs)

        layout = fxt_layoutf(fxt_config)
        layout["files"]["templates/page.html"] = "{{ unit.raw_text}"
        create_project_fixture(fs, layout)

        result = runner.invoke(main, ["build"])
        assert result.exit_code != 0
        assert "template 'page.html' has syntax errors" in result.output

        assert {f.name for f in fs.iterdir()} == \
            {"assets", "contents", "templates", "Volt.toml"}
