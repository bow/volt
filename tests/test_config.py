# -*- coding: utf-8 -*-
"""
    Tests for volt.config
    ~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

import pytest

from volt.config import validate_site_conf, SiteConfig, CONFIG_FNAME


def test_site_config_from_toml(tmpdir):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        cf = tmpdir.join(CONFIG_FNAME)
        cf.write("[site]\n", mode="a")
        cf.write('name = "ts"\n', mode="a")
        cf.write('url = "https://test.com"', mode="a")
        sc, errs = SiteConfig.from_toml(pwd, str(cf))

    assert not errs
    assert sc.pwd == pwd
    assert sc.contents_src == pwd.joinpath("contents")
    assert sc.templates_src == pwd.joinpath("templates")
    assert sc.assets_src == pwd.joinpath("assets")
    assert sc.site_dest == pwd.joinpath("site")
    assert sc.dot_html_url
    assert sc.timezone is not None
    assert sc.name == "ts"
    assert sc.url == "https://test.com"


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
    vres = validate_site_conf(site_conf)
    assert vres.is_success
    assert vres.data == site_conf


@pytest.mark.parametrize("config, exp_msg", [
    *[(v, "site config must be a mapping")
      for v in (12, 3.5, True, [])],

    *[({key: value}, f"site config {key!r} must be a nonempty string")
      for key in ("timezone", "unit", "unit_template",
                  "contents_src", "templates_src", "assets_src", "site_dest")
      for value in (12, 3.5, True, [], {})],

    *[({key: "/a/b"}, f"site config {key!r} must be a relative path")
      for key in ("contents_src", "templates_src", "assets_src", "site_dest")],

    *[({key: value}, f"site config {key!r} must be a boolean")
      for key in ("dot_html_url", "hide_first_pagination_idx")
      for value in (12, 3.5, "yes", [], {})],

    *[({"section": value}, f"section config must be a mapping")
      for value in (12, 3.5, True, "yes", [])],
])
def test_validate_site_conf_fail(config, exp_msg):
    robs = validate_site_conf(config)
    assert robs.is_failure, robs
    assert robs.errs == exp_msg
