# -*- coding: utf-8 -*-
"""
    Tests for volt.utils
    ~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
from pathlib import Path

import pytest
from pendulum.tz import local_timezone
from pendulum.tz.timezone import Timezone

from volt import exceptions as exc
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
    obj = import_mod_attr(istr)
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
        obj = import_mod_attr(istr)
        inst = obj()
        assert inst.val == 1


def test_import_mod_attr_fail_invalid_target():
    with pytest.raises(
        exc.VoltResourceError,
        match="invalid module attribute import target: 'os'",
    ):
        import_mod_attr("os")


@pytest.mark.parametrize("suffix", [":Test", ".Test"])
def test_import_mod_attr_fail_from_file(tmpdir, mod_toks, suffix):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_path = pwd.joinpath(*mod_toks)
        mod_path.mkdir(parents=True)
        target = mod_path.joinpath("custom.py")
        target.write_text("class Test:\n\tval = 1")
        with pytest.raises(
            exc.VoltResourceError,
            match="import from file is not yet supported",
        ):
            import_mod_attr(str(target) + suffix)


def test_import_mod_attr_fail_nonexistent(tmpdir, mod_toks):
    with tmpdir.as_cwd():
        with pytest.raises(
            exc.VoltResourceError,
            match="failed to import 'foo.bar.baz.custom'"
        ):
            import_mod_attr("foo.bar.baz.custom:Test")


def test_import_mod_attr_fail_attribute_missing(tmpdir, mod_toks):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_path = pwd.joinpath(*mod_toks)
        mod_path.mkdir(parents=True)
        target = mod_path.joinpath("custom.py")
        target.write_text("class Test:\n\tval = 1")
        msg = "module 'foo.bar.baz.custom' does not contain attribute 'Bzzt'"
        with pytest.raises(exc.VoltResourceError, match=msg):
            import_mod_attr("foo.bar.baz.custom.Bzzt")


@pytest.mark.parametrize("tzname, exp_tz", [
    (None, local_timezone()),
    ("Asia/Jakarta", Timezone("Asia/Jakarta")),
])
def test_get_tz_ok(tzname, exp_tz):
    obs_tz = get_tz(tzname)
    assert exp_tz.name == obs_tz.name


def test_get_tz_fail():
    with pytest.raises(
        exc.VoltTimezoneError,
        match="timezone 'bzzt' is invalid"
    ):
        get_tz("bzzt")


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


@pytest.mark.parametrize("target, ref", [
    (Path("a"), Path("a/b")),
    (Path("a/b"), Path("a")),
    (Path("/a"), Path("a/b")),
    (Path("a"), Path("/a/b")),
])
def test_calc_relpath_fail(target, ref):
    with pytest.raises(
        ValueError,
        match="could not compute relative paths of non-absolute input paths",
    ):
        calc_relpath(target, ref)
