# -*- coding: utf-8 -*-
"""
    Tests for volt.site
    ~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from volt import exceptions as exc
from volt import site
from volt.config import SiteConfig
from volt.targets import Target
from .utils import create_fs_fixture


class MockTarget(Target):

    def __init__(self, dest=None) -> None:
        self._dest = Path("site/out.html") if dest is None else Path(dest)

    @property
    def dest(self) -> Path:
        return self._dest

    def create(self) -> None:
        return None


def test_site_node_no_target():
    p = Path("/fs")
    sn = site.SiteNode(p)
    assert sn.path == p
    assert sn.target is None
    assert sn.children == {}
    assert sn.is_dir

    assert "key" not in sn
    assert list(iter(sn)) == []
    c1 = MockTarget()
    sn.add_child("key", c1)
    assert "key" in sn
    children = list(iter(sn))
    assert len(children) == 1

    child = children.pop()
    assert child.path == p.joinpath("key")
    assert child.target == c1
    assert child.children is None
    assert not child.is_dir


def test_site_node_with_target():
    p = Path("/fs")
    t = MockTarget()
    sn = site.SiteNode(p, target=t)
    assert sn.path == p
    assert sn.target == t
    assert sn.children is None
    assert not sn.is_dir

    assert "key" not in sn
    assert list(iter(sn)) == []
    with pytest.raises(TypeError, match="cannot add children to file node"):
        sn.add_child("test", MockTarget())
    assert "key" not in sn
    assert list(iter(sn)) == []


def test_site_node_add_children_existing_key():
    p = Path("/fs")
    sn = site.SiteNode(p)
    c1 = MockTarget("s/1")
    c2 = MockTarget("s/2")
    sn.add_child("key", c1)
    sn.add_child("key", c2)
    assert len(list(iter(sn))) == 1
    assert list(iter(sn))[0].target == c1


@pytest.mark.parametrize("targets, dpaths, fpaths", [
    ([], [], []),
    (
        ["site/a", "site/b", "site/c"],
        ["site"],
        ["site/a", "site/b", "site/c"],
    ),
    (
        ["site/a/aa", "site/a/ab", "site/b"],
        ["site/a"],
        ["site/a/aa", "site/a/ab", "site/b"],
    ),
    (
        ["site/a/aa", "site/a/ab", "site/b/ab", "site/b/bb/bbb"],
        ["site/a", "site/b/bb"],
        ["site/a/aa", "site/a/ab", "site/b/ab", "site/b/bb/bbb"],
    ),
    (
        ["site/a/aa", "site/b/bb", "site/c/cc"],
        ["site/c", "site/b", "site/a"],
        ["site/a/aa", "site/b/bb", "site/c/cc"],
    ),
])
def test_site_plan_ok(targets, dpaths, fpaths):
    sp = site.SitePlan(Path("site"))
    for target in targets:
        res = sp.add_target(MockTarget(target))
        assert res is None

    assert sorted([n.path for n in sp.dnodes()]) == (
        sorted([Path(dp) for dp in dpaths])
    )
    assert sorted([n.path for n in sp.fnodes()]) == (
        sorted([Path(fp) for fp in fpaths])
    )


@pytest.mark.parametrize("target1, target2, exp_msg", [
    ("site/a", "site/a/b",
     "path of target item 'site/a/b' conflicts with 'site/a'"),
])
def test_site_plan_fail(target1, target2, exp_msg):
    sp = site.SitePlan(Path("site"))
    sp.add_target(MockTarget(target1))
    with pytest.raises(ValueError, match=exp_msg):
        sp.add_target(MockTarget(target2))


@pytest.mark.parametrize("files", [
    {},
    {f"contents/{name}.md": f"---\ntitle: {name}\n---\n\nFoo"
     for name in ["c1", "c2", "c3"]}
])
def test_site_gather_units_ok(files):
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents"],
            "files": files
        })
        s = site.Site(SiteConfig(fs, fs))

        units = s.gather_units()
        fnames = [fn.rsplit("/", 1)[1] for fn in files]
        assert len(units) == len(fnames)
        assert sorted([u.src.name for u in units]) == sorted(fnames)


def test_site_gather_units_fail():
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents"],
            "files": {
                "contents/fail.md": "---",
                **{f"contents/{name}.md": f"---\ntitle: {name}\n---\n\nFoo"
                   for name in ["c1", "c2", "c3"]}
            }
        })
        s = site.Site(SiteConfig(fs, fs))

        with pytest.raises(
            exc.VoltResourceError,
            match="malformed unit: 'contents/fail.md'"
        ):
            s.gather_units()


def test_site_create_pages_ok():
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents", "templates"],
            "files": {
                "contents/ok.md": "---\ntitle: ok\n---\nFoo",
                "templates/page.html": "{{ unit.raw_text }}"
            }
        })
        s = site.Site(SiteConfig(fs, fs))

        pages = s.create_pages(s.gather_units())
        assert len(pages) == 1
        page = pages.pop()
        assert page.dest == Path("site/ok.html")


def test_site_create_pages_fail_no_template():
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents", "templates"],
            "files": {
                "contents/ok.md": "---\ntitle: ok\n---\n\nFoo",
            }
        })
        s = site.Site(SiteConfig(fs, fs))

        with pytest.raises(
            exc.VoltResourceError,
            match="could not find template 'page.html'",
        ):
            s.create_pages(s.gather_units())


def test_site_create_pages_fail_template_error():
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents", "templates"],
            "files": {
                "contents/ok.md": "---\ntitle: ok\n---\n\nFoo",
                "templates/page.html": "{{ unit.raw_text"
            }
        })
        s = site.Site(SiteConfig(fs, fs))

        with pytest.raises(
            exc.VoltResourceError,
            match="template 'page.html' has syntax errors",
        ):
            s.create_pages(s.gather_units())


def test_site_create_pages_fail_page_error():
    with TemporaryDirectory() as td:
        fs = Path(td)

        create_fs_fixture(fs, {
            "dirs": ["contents", "templates"],
            "files": {
                "contents/ok.md": "---\ntitle: ok\n---\n\nFoo",
                "templates/page.html": "{{ foo.bzzt }}"
            }
        })
        s = site.Site(SiteConfig(fs, fs))

        with pytest.raises(
            exc.VoltResourceError,
            match="could not render to 'site/ok.html' using 'page.html'"
        ):
            s.create_pages(s.gather_units())
