# -*- coding: utf-8 -*-
"""
    Tests for volt.targets
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pendulum import datetime as dt
from pendulum.tz.timezone import Timezone

from volt import exceptions as exc
from volt.config import SiteConfig
from volt.units import Unit, validate_metadata


@pytest.mark.parametrize("meta, exp_msg", [
    *[(v, "unit metadata must be a mapping")
      for v in (12, 3.5, True, "yes", [])],

    *[({key: value}, f"unit metadata {key!r} must be a nonempty string")
      for key in ("title", "slug")
      for value in (12, 3.5, True, "", [], {})],

    *[({"tags": value}, "unit metadata 'tags' must be a string or a list")
      for value in (12, 3.5, True, {})],

    *[({"pub_time": value},
       "unit metadata 'pub_time' must be a valid iso8601 timestamp")
      for value in (12, 3.5, True, "yes", [], {})],
])
def test_validate_metadata_fail(meta, exp_msg):
    with pytest.raises(exc.VoltResourceError, match=exp_msg):
        validate_metadata(meta)


@pytest.mark.parametrize("raw, fname, exp", [
    ("---\n", "test.md", {"slug": "test", "title": "test"}),
    ("---\ntags: a, b", "test.md",
     {"tags": ["a", "b"], "slug": "test", "title": "test"}),
    ("---\ntags:\n  - a\n  - b", "test.md",
     {"tags": ["a", "b"], "slug": "test", "title": "test"}),
])
def test_unit_parse_metadata_ok_simple(raw, fname, exp):
    cwd = pwd = Path("/fs")
    unit = Unit.parse_metadata(raw, SiteConfig(cwd, pwd), cwd.joinpath(fname))
    assert unit == exp


def test_unit_parse_metadata_ok_pub_time_no_config_tz():
    cwd = pwd = Path("/fs")
    meta = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 01:02:03", SiteConfig(cwd, pwd),
        cwd.joinpath("test.md"))
    assert meta == {
        "title": "test",
        "slug": "test",
        "pub_time": dt(2018, 6, 3, 1, 2, 3),
    }


def test_unit_parse_metadata_ok_pub_time_with_config_tz():
    cwd = pwd = Path("/fs")
    tz = Timezone("Africa/Tripoli")
    meta = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 01:02:03",
        SiteConfig(cwd, pwd, timezone=tz), cwd.joinpath("test.md"))
    assert meta == {
        "title": "test",
        "slug": "test",
        "pub_time": dt(2018, 6, 3, 1, 2, 3, tz=tz),
    }


def test_unit_parse_metadata_ok_pub_time_with_config_and_unit_tz():
    cwd = pwd = Path("/fs")
    tz = Timezone("Africa/Tripoli")
    meta = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 21:02:03+05:00",
        SiteConfig(cwd, pwd, timezone=tz), cwd.joinpath("test.md"))
    utc = Timezone("UTC")
    assert dt(2018, 6, 3, 16, 2, 3, tz=utc) == utc.convert(meta.pop("pub_time"))
    assert meta == {
        "title": "test",
        "slug": "test",
    }


def test_unit_parse_metadata_custom_slug():
    cwd = pwd = Path("/fs")
    meta = Unit.parse_metadata(
        "---\nslug: My Custom Slug", SiteConfig(cwd, pwd),
        cwd.joinpath("test.md"))
    assert meta == {
        "title": "test",
        "slug": "my-custom-slug",
    }


def test_unit_parse_metadata_fail():
    cwd = pwd = Path("/fs")
    with pytest.raises(exc.VoltResourceError, match="malformed metadata"):
        Unit.parse_metadata(
            "---\nbzzt: {",
            SiteConfig(cwd, pwd),
            Path("/fs/contents/01.md"),
        )


def test_unit_load_fail_read_bytes():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.side_effect = OSError
    cwd = pwd = Path("/fs")
    with pytest.raises(exc.VoltResourceError, match="could not load unit"):
        Unit.load(src, SiteConfig(cwd, pwd))


def test_unit_load_fail_invalid_encoding():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "foo".encode("utf-8")
    cwd = pwd = Path("/fs")
    with pytest.raises(
        exc.VoltResourceError,
        match=r"could not decode unit .+ using 'utf-16' as encoding",
    ):
        Unit.load(src, SiteConfig(cwd, pwd), encoding="utf-16")


def test_unit_load_fail_unknown_encoding():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "foo".encode("utf-8")
    cwd = pwd = Path("/fs")
    with pytest.raises(
        exc.VoltResourceError,
        match=r"could not decode unit .+ 'utf-100': unknown encoding"
    ):
        Unit.load(src, SiteConfig(cwd, pwd), encoding="utf-100")


def test_unit_load_fail_malformed_unit():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "---\ntitle: {---\n\nFoo".encode("utf-8")
    cwd = pwd = Path("/fs")
    with pytest.raises(exc.VoltResourceError, match="malformed unit"):
        Unit.load(src, SiteConfig(cwd, pwd))


def test_unit_load_fail_parse_metadata():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = \
        "---\ntitle: foo\npub_time: 2018-06-12T5 \n---\n\nFoo".encode("utf-8")
    cwd = pwd = Path("/fs")
    with pytest.raises(
        exc.VoltResourceError,
        match="unit metadata 'pub_time' must be a valid iso8601 timestamp",
    ):
        Unit.load(src, SiteConfig(cwd, pwd))
