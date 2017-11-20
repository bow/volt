# -*- coding: utf-8 -*-
"""
    Tests for volt.config
    ~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

from volt.config import SiteConfig, CONFIG_FNAME


def test_from_toml(tmpdir):
    with tmpdir.as_cwd():
        wp = Path(str(tmpdir))
        cf = tmpdir.join(CONFIG_FNAME)
        cf.write("[site]\n", mode="a")
        cf.write('name = "ts"\n', mode="a")
        cf.write('url = "https://test.com"', mode="a")
        c, errs = SiteConfig.from_toml(wp, str(cf))

    assert errs == []
    assert c.work_path == wp
    assert c.contents_path == wp.joinpath("contents")
    assert c.templates_path == wp.joinpath("templates")
    assert c.assets_path == wp.joinpath("templates", "assets")
    assert c.site_path == wp.joinpath("site")
    assert c["dot_html_url"]
    assert c["name"] == "ts"
    assert c["url"] == "https://test.com"
    assert "site" not in c
