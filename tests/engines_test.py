"""Tests for volt.engines."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest

from volt.engines import _calc_relpath


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
def test__calc_relpath_ok(target, ref, exp):
    obs = _calc_relpath(target, ref)
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
def test__calc_relpath_fail(target, ref):
    with pytest.raises(
        ValueError,
        match="could not compute relative paths of non-absolute input paths",
    ):
        _calc_relpath(target, ref)
