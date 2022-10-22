"""Tests for volt.utils."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
from pathlib import Path

import pytest

from volt import error as err
from volt.utils import calc_relpath, import_file


def test_import_file_ok(tmpdir):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_fp = pwd.joinpath("custom.py")
        mod_fp.write_text("class Test:\n\tval = 1")
        mod = import_file(mod_fp, "volt.test.custom")

        assert hasattr(mod, "Test")
        cls = getattr(mod, "Test")
        inst = cls()
        assert inst.val == 1


def test_import_file_err_not_importable(tmpdir):
    with tmpdir.as_cwd():
        pwd = Path(str(tmpdir))
        mod_fp = pwd.joinpath("custom.txt")
        mod_fp.write_text("foobar")

        with pytest.raises(err.VoltResourceError, match="not an importable file:"):
            import_file(mod_fp, "volt.test.custom")


@pytest.mark.parametrize(
    "target, ref, exp",
    [
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
    ],
)
def test_calc_relpath_ok(target, ref, exp):
    obs = calc_relpath(target, ref)
    assert obs == exp


@pytest.mark.parametrize(
    "target, ref",
    [
        (Path("a"), Path("a/b")),
        (Path("a/b"), Path("a")),
        (Path("/a"), Path("a/b")),
        (Path("a"), Path("/a/b")),
    ],
)
def test_calc_relpath_fail(target, ref):
    with pytest.raises(
        ValueError,
        match="could not compute relative paths of non-absolute input paths",
    ):
        calc_relpath(target, ref)
