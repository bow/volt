# -*- coding: utf-8 -*-
"""
    Tests for volt.utils
    ~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path

import pytest
import pytz
import tzlocal

from volt.utils import calc_relpath, get_tz, import_mod_attr


@pytest.fixture
def mod_toks(request):
    toks = ["foo", "bar", "baz"]

    def finalizer():
        import sys
        mod_paths = [".".join(toks[:i]) for i in range(1, len(toks) + 1)]
        for mod_path in mod_paths:
            try:
                del sys.modules[mod_path]
            except KeyError:
                pass

    request.addfinalizer(finalizer)

    yield toks


@pytest.mark.parametrize("istr", [
    "os.mkdir", "os:mkdir"
])
def test_import_mod_attr_ok(istr):
    import os
    obj, errs = import_mod_attr(istr)
    assert not errs
    assert obj is os.mkdir


@pytest.mark.parametrize("istr", [
    "foo.bar.baz.custom.Test", "foo.bar.baz.custom:Test"
])
def test_import_mod_attr_ok_custom(istr, mod_toks, tmpdir):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_path = pwd.joinpath(*mod_toks)
        mod_path.mkdir(parents=True)
        target = mod_path.joinpath("custom.py")
        target.write_text("class Test:\n\tval = 1")
        obj, errs = import_mod_attr(istr)
        assert not errs
        inst = obj()
        assert inst.val == 1


def test_import_mod_attr_fail_invalid_target():
    _, errs = import_mod_attr("os")
    assert errs == "invalid module attribute import target: 'os'"


@pytest.mark.parametrize("suffix", [":Test", ".Test"])
def test_import_mod_attr_fail_from_file(tmpdir, mod_toks, suffix):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_path = pwd.joinpath(*mod_toks)
        mod_path.mkdir(parents=True)
        target = mod_path.joinpath("custom.py")
        target.write_text("class Test:\n\tval = 1")
        _, errs = import_mod_attr(str(target) + suffix)
        assert errs == "import from file is not yet supported"


def test_import_mod_attr_fail_nonexistent(tmpdir, mod_toks):
    with tmpdir.as_cwd():
        obj, errs = import_mod_attr("foo.bar.baz.custom:Test")
        assert errs == "failed to find module 'foo.bar.baz.custom' for import"


def test_import_mod_attr_fail_attribute_missing(tmpdir, mod_toks):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_path = pwd.joinpath(*mod_toks)
        mod_path.mkdir(parents=True)
        target = mod_path.joinpath("custom.py")
        target.write_text("class Test:\n\tval = 1")
        obj, errs = import_mod_attr("foo.bar.baz.custom.Bzzt")
        assert errs == "module 'foo.bar.baz.custom' does not contain" + \
                       " attribute 'Bzzt'"


@pytest.mark.parametrize("tzname, exp_data", [
    (None, tzlocal.get_localzone()),
    ("Asia/Jakarta", pytz.timezone("Asia/Jakarta")),
])
def test_get_tz_ok(tzname, exp_data):
    obs_data, obs_errs = get_tz(tzname)
    assert not obs_errs
    assert obs_data == exp_data


def test_get_tz_fail():
    obs_data, obs_errs = get_tz("bzzt")
    assert not obs_data
    assert obs_errs == "cannot interpret timezone 'bzzt'"


@pytest.mark.parametrize("target, ref, exp", [
    # target is the same as ref
    (Path("/a"), Path("/a"), Path(".")),
    (Path("/a/b"), Path("/a/b"), Path(".")),

    # target is a child of ref
    (Path("/a/b"), Path("/a"), Path("b")),
    (Path("/a/b/c"), Path("/a/b"), Path("c")),
    (Path("/a/b/c"), Path("/a"), Path("b/c")),

    # target is a sibling of ref
    (Path("/b"), Path("/a"), Path("../b")),
    (Path("/a/c"), Path("/a/b"), Path("../c")),

    # target and ref shares a common parent
    (Path("/a/b/c"), Path("/a/d/f"), Path("../../b/c/")),
    (Path("/a/b/c/d"), Path("/a/b/d/x/z/q"), Path("../../../../c/d")),
    (Path("/a/b/c/d/e/f"), Path("/a/x/y/z"), Path("../../../b/c/d/e/f")),
])
def test_calc_relpath_ok(target, ref, exp):
    obs = calc_relpath(target, ref)
    assert obs == exp


@pytest.mark.parametrize("target, ref, msg", [
    (Path("a"), Path("a/b"), "cannot compute relative paths of non-absolute"
                             " input paths"),
    (Path("a/b"), Path("a"), "cannot compute relative paths of non-absolute"
                             " input paths"),
    (Path("/a"), Path("a/b"), "cannot compute relative paths of non-absolute"
                              " input paths"),
    (Path("a"), Path("/a/b"), "cannot compute relative paths of non-absolute"
                              " input paths"),
])
def test_calc_relpath_fail(target, ref, msg):
    with pytest.raises(ValueError, match=msg):
        calc_relpath(target, ref)
