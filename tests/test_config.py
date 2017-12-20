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
    assert sc.static_src == pwd.joinpath("static")
    assert sc.site_dest == pwd.joinpath("site")
    assert sc.dot_html_url
    assert sc.timezone is not None
    assert sc.name == "ts"
    assert sc.url == "https://test.com"
