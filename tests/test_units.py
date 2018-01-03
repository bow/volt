# -*- coding: utf-8 -*-
"""
    Tests for volt.targets
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from datetime import datetime as dt
from pathlib import Path
from unittest.mock import create_autospec

import pytest
import pytz

from volt.config import SiteConfig
from volt.units import validate_metadata, Unit


def test_validate_metadata_ok():
    pass


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
    vres = validate_metadata(meta)
    assert vres.is_failure
    assert vres.errs == exp_msg


@pytest.mark.parametrize("raw, fname, exp", [
    ("---\n", "test.md", {"slug": "test", "title": "test"}),
    ("---\ntags: a, b", "test.md",
     {"tags": ["a", "b"], "slug": "test", "title": "test"}),
    ("---\ntags:\n  - a\n  - b", "test.md",
     {"tags": ["a", "b"], "slug": "test", "title": "test"}),
])
def test_unit_parse_metadata_ok_simple(raw, fname, exp):
    cwd = Path("/fs")
    ures = Unit.parse_metadata(raw, SiteConfig(cwd), cwd.joinpath(fname))
    assert ures.is_success, ures
    assert ures.data == exp, ures


def test_unit_parse_metadata_ok_pub_time_no_config_tz():
    cwd = Path("/fs")
    ures = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 01:02:03", SiteConfig(cwd),
        cwd.joinpath("test.md"))
    assert ures.is_success, ures
    assert ures.data == {
        "title": "test",
        "slug": "test",
        "pub_time": dt(2018, 6, 3, 1, 2, 3),
    }


def test_unit_parse_metadata_ok_pub_time_with_config_tz():
    cwd = Path("/fs")
    tz = pytz.timezone("Africa/Tripoli")
    ures = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 01:02:03", SiteConfig(cwd, timezone=tz),
        cwd.joinpath("test.md"))
    assert ures.is_success, ures
    assert ures.data == {
        "title": "test",
        "slug": "test",
        "pub_time": tz.localize(dt(2018, 6, 3, 1, 2, 3)),
    }


def test_unit_parse_metadata_ok_pub_time_with_config_and_unit_tz():
    cwd = Path("/fs")
    tz = pytz.timezone("Africa/Tripoli")
    ures = Unit.parse_metadata(
        "---\npub_time: 2018-06-03 21:02:03+05:00",
        SiteConfig(cwd, timezone=tz), cwd.joinpath("test.md"))
    assert ures.is_success, ures
    assert ures.data == {
        "title": "test",
        "slug": "test",
        "pub_time": tz.localize(dt(2018, 6, 3, 16, 2, 3)),
    }


def test_unit_parse_metadata_custom_slug():
    cwd = Path("/fs")
    ures = Unit.parse_metadata(
        "---\nslug: My Custom Slug", SiteConfig(cwd), cwd.joinpath("test.md"))
    assert ures.is_success, ures
    assert ures.data == {
        "title": "test",
        "slug": "my-custom-slug",
    }


def test_unit_parse_metadata_fail():
    cwd = Path("/fs")
    ures = Unit.parse_metadata("---\nbzzt: {", SiteConfig(cwd),
                               Path("/fs/contents/01.md"))
    assert ures.is_failure
    assert ures.errs.startswith("malformed metadata")


def test_unit_load_fail_read_bytes():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.side_effect = OSError
    ures = Unit.load(src, SiteConfig(Path("/fs")))
    assert ures.is_failure, ures
    assert ures.errs.startswith("cannot load unit")


def test_unit_load_fail_invalid_encoding():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "foo".encode("utf-8")
    ures = Unit.load(src, SiteConfig(Path("/fs")), encoding="utf-16")
    assert ures.is_failure, ures
    assert ures.errs.startswith("cannot decode unit")
    assert ures.errs.endswith("using 'utf-16'")


def test_unit_load_fail_unknown_encoding():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "foo".encode("utf-8")
    ures = Unit.load(src, SiteConfig(Path("/fs")), encoding="utf-100")
    assert ures.is_failure, ures
    assert ures.errs.startswith("cannot decode unit")
    assert ures.errs.endswith("unknown encoding")


def test_unit_load_fail_malformed_unit():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = "---\ntitle: {---\n\nFoo".encode("utf-8")
    ures = Unit.load(src, SiteConfig(Path("/fs")))
    assert ures.is_failure, ures
    assert ures.errs.startswith("malformed unit")


def test_unit_load_fail_parse_metadata():
    src = create_autospec(Path, spec_set=True)
    src.read_bytes.return_value = \
        "---\ntitle: foo\npub_time: 2018-06-12T5 \n---\n\nFoo".encode("utf-8")
    ures = Unit.load(src, SiteConfig(Path("/fs")))
    assert ures.is_failure, ures
    assert ures.errs.startswith("unit metadata 'pub_time' must be a valid"
                                " iso8601 timestamp")
