# -*- coding: utf-8 -*-
"""
    Tests for volt.config
    ~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

import pytest
from pendulum.tz.timezone import Timezone

from volt import config as conf
from volt import exceptions as exc


def test_validate_site_conf_ok():
    site_conf = {
        "timezone": "Europe/Amsterdam",
        "unit": "volt.units.Unit",
        "unit_template": "page.html",
        "contents_src": "contents",
        "templates_src": "templates",
        "assets_src": "assets",
        "site_dest": "site",
        "dot_html_url": False,
        "hide_first_pagination_idx": True,
        "section": {},
        "custom": {"user_supplied": 123},
    }
    ret = conf.validate_site_conf(site_conf)
    assert ret is None


@pytest.mark.parametrize("config, exp_msg", [
    *[(v, "site config must be a mapping")
      for v in (12, 3.5, True, "yes", [])],

    *[({key: value}, f"site config {key!r} must be a string")
      for key in ("name", "url")
      for value in (12, 3.5, True, [], {})],

    *[({key: value}, f"site config {key!r} must be a nonempty string")
      for key in ("timezone", "unit", "unit_template",
                  "contents_src", "templates_src", "assets_src", "site_dest")
      for value in (12, 3.5, True, "", [], {})],

    *[({key: "/a/b"}, f"site config {key!r} must be a relative path")
      for key in ("contents_src", "templates_src", "assets_src", "site_dest")],

    *[({key: value}, f"site config {key!r} must be a boolean")
      for key in ("dot_html_url", "hide_first_pagination_idx")
      for value in (12, 3.5, "yes", [], {})],

    *[({"section": value}, "section config must be a mapping")
      for value in (12, 3.5, True, "yes", [])],
])
def test_validate_site_conf_fail(config, exp_msg):
    with pytest.raises(exc.VoltConfigError, match=exp_msg):
        conf.validate_site_conf(config)


def test_validate_section_conf_ok():
    section_conf = {
        "dot_html_url": True,
        "hide_first_pagination_idx": False,
        "pagination_size": 10,
        "path": "/foo",
        "engine": "foo.FooEngine",
        "unit_template": "foo.html",
        "unit_path_patten": "/foo/{slug}",
        "pagination_template": "foop.html",
        "contents_src": "contents",
        "paginations": {"p": {"path_pattern": "{idx}"}},
        "unit_order": {"key": "title"},
        "custom": {"user_supplied": 123},
    }
    ret = conf.validate_section_conf("foo", section_conf)
    assert ret is None


@pytest.mark.parametrize("name, config, exp_msg", [
    *[("foo", v, "section config 'foo' must be a mapping")
      for v in (12, 3.5, True, "yes", [])],

    *[("foo", {key: value},
       f"config {key!r} of section 'foo' must be a boolean")
      for key in ("dot_html_url", "hide_first_pagination_idx")
      for value in (12, 3.5, "yes", [], {})],

    *[("foo", {key: value},
       f"config {key!r} of section 'foo' must be a positive, nonzero integer")
      for key in ("pagination_size",)
      for value in (-1, 0, True, "yes", [], {})],

    *[("foo", {key: value},
       f"config {key!r} of section 'foo' must be a nonempty string")
      for key in ("path", "engine", "unit", "unit_template",
                  "pagination_template", "contents_src")
      for value in (12, 3.5, True, "", [], {})],

    *[("foo", {key: "/a/b"},
       f"config {key!r} of section 'foo' must be a relative path")
      for key in ("contents_src", "unit_path_pattern")],

    ("foo", {"paginations": {"pg": {}}},
     "config 'paginations.pg.path_pattern' of section 'foo' must be present"),
])
def test_validate_section_conf_fail(name, config, exp_msg):
    with pytest.raises(exc.VoltConfigError, match=exp_msg):
        conf.validate_section_conf(name, config)


@pytest.mark.parametrize("section_conf", [
    {},
    {"paginations": {
        "foo": {
            "path_pattern": "{idx}",
            "size": 10,
            "pagination_template": "foo.html",
        }}}
])
def test_validate_section_pagination_ok(section_conf):
    ret = conf.validate_section_pagination("foo", section_conf, "paginations")
    assert ret is None


@pytest.mark.parametrize("section_conf", [
    {},
    {"unit_order": {"key": "pub_time", "reverse": True}},
])
def test_validate_section_unit_order_ok(section_conf):
    ret = conf.validate_section_unit_order("foo", section_conf, "unit_orders")
    assert ret is None


@pytest.mark.parametrize("name, pgn_config, exp_msg", [
    *[("foo", v, "config 'paginations' of section 'foo' must be a mapping",)
      for v in (12, 3.5, True, "yes", [])],

    ("foo", {"pg": {}},
     "config 'paginations.pg.path_pattern' of section 'foo' must be present"),

    *[("foo", {"pg": {"path_pattern": value}},
       "config 'paginations.pg.path_pattern' of section 'foo' must be a"
       " nonempty string")
      for value in (12, 3.5, True, "", [], {})],

    ("foo", {"pg": {"path_pattern": "{bzzzt}"}},
     "config 'paginations.pg.path_pattern' of section 'foo' must contain the"
     " '{idx}' wildcard"),

    *[("foo", {"pg": {"path_pattern": "{idx}", "size": value}},
       "config 'paginations.pg.size' of section 'foo' must be a positive,"
       " nonzero integer")
      for value in (-1, 0, True, "yes", [], {})],

    *[("foo", {"pg": {"path_pattern": "{idx}", "pagination_template": value}},
       "config 'paginations.pg.pagination_template' of section 'foo' must be a"
       " nonempty string")
      for value in (12, 3.5, True, "", [], {})],
])
def test_validate_section_pagination_fail(name, pgn_config, exp_msg):
    with pytest.raises(exc.VoltConfigError, match=exp_msg):
        conf.validate_section_pagination(
            name,
            {"paginations": pgn_config},
            "paginations",
        )


@pytest.mark.parametrize("name, uu_config, exp_msg", [
    *[("foo", v, "config 'unit_order' of section 'foo' must be a mapping",)
      for v in (12, 3.5, True, "yes", [])],

    ("foo", {}, "config 'unit_order.key' of section 'foo' must be present"),

    *[("foo", {"key": value},
       "config 'unit_order.key' of section 'foo' must be a nonempty string")
      for value in (12, 3.5, True, "", [], {})],

    *[("foo", {"key": "p", "reverse": value},
       "config 'unit_order.reverse' of section 'foo' must be a boolean")
      for value in (12, 3.5, "yes", [], {})],
])
def test_validate_section_unit_order_fail(name, uu_config, exp_msg):
    with pytest.raises(exc.VoltConfigError, match=exp_msg):

        conf.validate_section_unit_order(
            name,
            {"unit_order": uu_config},
            "unit_order",
        )


def test_site_config_from_yaml_ok(tmpdir):
    with tmpdir.as_cwd():
        cwd = pwd = Path(str(tmpdir))
        cf = tmpdir.join(conf.CONFIG_FNAME)
        cf.write("""site:
  name: ts
  url: https://test.com
""")
        sc = conf.SiteConfig.from_yaml(cwd, pwd, str(cf))

    assert sc["cwd"] == cwd
    assert sc["pwd"] == pwd
    assert sc["contents_src"] == pwd.joinpath("contents")
    assert sc["templates_src"] == pwd.joinpath("templates")
    assert sc["assets_src"] == pwd.joinpath("assets")
    assert sc["site_dest"] == pwd.joinpath("site")
    assert sc["dot_html_url"]
    assert sc["timezone"] is not None
    assert sc["name"] == "ts"
    assert sc["url"] == "https://test.com"


def test_site_config_from_yaml_fail(tmpdir):
    with tmpdir.as_cwd():
        cwd = pwd = Path(str(tmpdir))
        cf = tmpdir.join(conf.CONFIG_FNAME)
        cf.write("[site][\n")
        with pytest.raises(
            exc.VoltConfigError,
            match="could not parse config: "
        ):
            conf.SiteConfig.from_yaml(cwd, pwd, str(cf))


def test_site_config_from_raw_config_ok():
    user_config = {
        "site": {
            "name": "",
            "url": "",
            "timezone": "Europe/Amsterdam",
        },
        "section": {"pg": {}},
    }
    cwd = pwd = Path("/fs")
    sc = conf.SiteConfig.from_raw_config(cwd, pwd, user_config)
    exp_site = {
        "name": "",
        "url": "",
        "timezone": Timezone("Europe/Amsterdam"),
        "pwd": pwd,
        "cwd": cwd,
        "contents_src": pwd.joinpath("contents"),
        "templates_src": pwd.joinpath("templates"),
        "assets_src": pwd.joinpath("assets"),
        "site_dest": pwd.joinpath("site"),
        "site_dest_rel": Path("site"),
        "dot_html_url": True,
        "hide_first_pagination_idx": True,
        "unit_template": "page.html",
        "sections": {
        }
    }
    exp_section = {
        "name": "pg",
        "paginations": {},
        "pagination_size": 10,
        "unit_order": {"key": "pub_time", "reverse": True},
        "dot_html_url": True,
        "hide_first_pagination_idx": True,
        "path": "/pg",
        "unit_path_pattern": "/pg/{slug}",
        "site_dest": pwd.joinpath("site", "pg"),
        "contents_src": pwd.joinpath("contents", "pg"),
        # Values that should be present in site config.
        "dot_html_url": True,
        "hide_first_pagination_idx": True,
    }
    # Because 'unit' is overwritten by the actual class.
    assert not isinstance(sc.pop("unit", ""), str)
    # Because 'site_config' shows up as a recursion.
    sec = sc["sections"].pop("pg")
    # Because timezones can not be compared for equality.
    assert sc.pop("timezone").name == exp_site.pop("timezone").name

    assert sc == exp_site

    for key, value in exp_section.items():
        assert key in sec, key
        assert sec[key] == value, value


@pytest.mark.parametrize("config, exc", [
    (
        {},
        exc.VoltConfigError("could not find site configuration in config file"),
    ),
    (
        {"site": {"name": 100}},
        exc.VoltConfigError("site config 'name' must be a string"),
    ),
    (
        {"site": {"timezone": "bzzt"}},
        exc.VoltTimezoneError("bzzt"),
    ),
    (
        {"site": {"unit": "bzzt"}},
        exc.VoltResourceError("invalid module attribute import target: 'bzzt'")
    ),
    (
        {"site": {}, "section": {"foo": True}},
        exc.VoltConfigError("section config 'foo' must be a mapping")
    ),
])
def test_site_config_from_raw_config_fail(config, exc):
    cwd = pwd = Path("/fs")
    with pytest.raises(exc.__class__, match=exc.message):
        conf.SiteConfig.from_raw_config(cwd, pwd, config)


@pytest.mark.parametrize("path, exp_path", [
    ("foo", "/foo"),
    ("/foo", "/foo"),
    (None, "/foo"),
])
def test_section_config_ok(path, exp_path):
    cwd = pwd = Path("/fs")
    site_config = conf.SiteConfig(cwd, pwd)
    raw_section_config = {
        "custom": "value",
        "path": path,
        "paginations": {"pg": {"path_pattern": "{idx}"}}
    }
    if path is None:
        raw_section_config.pop("path")
    section_config = conf.SectionConfig.from_raw_configs(
        "foo",
        raw_section_config,
        site_config,
    )
    exp_section = {
        "name": "foo",
        "paginations": {"pg": {"path_pattern": "{idx}", "size": 10}},
        "pagination_size": 10,
        "unit_order": {"key": "pub_time", "reverse": True},
        "dot_html_url": True,
        "hide_first_pagination_idx": True,
        "path": exp_path,
        "unit_path_pattern": "/foo/{slug}",
        "contents_src": cwd.joinpath("contents", "foo"),
        "site_dest": cwd.joinpath("site", "foo"),
        # Values that should be present in site config.
        "dot_html_url": True,
        "hide_first_pagination_idx": True,
        # Arbitrary key-value pairs set before.
        "custom": "value",
    }
    for key, value in exp_section.items():
        assert key in section_config, key
        assert section_config[key] == value, value
