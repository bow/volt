# -*- coding: utf-8 -*-
"""
    Tests for volt.config
    ~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

from volt.config import SessionConfig, CONFIG_FNAME


def test_from_toml(tmpdir):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        cf = tmpdir.join(CONFIG_FNAME)
        cf.write("[site]\n", mode="a")
        cf.write('name = "ts"\n', mode="a")
        cf.write('url = "https://test.com"', mode="a")
        sc, errs = SessionConfig.from_toml(pwd, str(cf))
        c = sc.site

    assert errs == []
    assert sc.pwd == pwd
    assert c.contents_src == pwd.joinpath("contents")
    assert c.templates_src == pwd.joinpath("templates")
    assert c.static_src == pwd.joinpath("static")
    assert c.site_dest == pwd.joinpath("site")
    assert c.dot_html_url
    assert c.name == "ts"
    assert c.url == "https://test.com"
    assert not hasattr(c, "site")
