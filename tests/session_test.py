"""Tests for volt.session."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

from volt import session

from . import utils as u


def test_new_ok_minimal(tmp_path: Path) -> None:
    u.assert_dir_empty(tmp_path)

    project_dir = session.new(
        dirname=None,
        invoc_dir=tmp_path,
        project_dir=tmp_path,
        name="",
        url="",
        author=None,
        description="",
        language=None,
        force=False,
        vcs=None,
    )

    assert project_dir == tmp_path

    theme_dir = project_dir / "theme"
    sources_dir = project_dir / "source"
    config_fp = project_dir / "volt.yaml"
    u.assert_dir_contains_only(project_dir, [theme_dir, sources_dir, config_fp])

    u.assert_dir_empty(theme_dir)

    static_dir = sources_dir / "static"
    u.assert_dir_contains_only(sources_dir, [static_dir])

    u.assert_dir_empty(static_dir)

    config = u.load_config(config_fp)
    assert u.has_and_pop(config, "language")
    assert u.has_and_pop(config, "author")
    assert config == {
        "name": "",
        "url": "",
        "description": "",
    }

    return None
