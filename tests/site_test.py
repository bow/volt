"""Tests for volt.site."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest

from volt import Output, site


class MockOutput(Output):
    def __init__(self, dest=None) -> None:
        self.url = dest if dest is not None else "site/out.html"

    def write(self, parent_dir: Path) -> None:
        return None


def test_site_node_no_output():
    p = Path("/fs")
    sn = site._PlanNode(p)
    assert sn.path == p
    assert sn.output is None
    assert sn.children == {}
    assert sn.is_dir

    assert "key" not in sn
    assert list(iter(sn)) == []
    c1 = MockOutput()
    sn.add_child("key", c1)
    assert "key" in sn
    children = list(iter(sn))
    assert len(children) == 1

    child = children.pop()
    assert child.path == p.joinpath("key")
    assert child.output == c1
    assert child.children is None
    assert not child.is_dir


def test_site_node_with_output():
    p = Path("/fs")
    o = MockOutput()
    sn = site._PlanNode(p, output=o)
    assert sn.path == p
    assert sn.output == o
    assert sn.children is None
    assert not sn.is_dir

    assert "key" not in sn
    assert list(iter(sn)) == []
    with pytest.raises(TypeError, match="cannot add children to file node"):
        sn.add_child("test", MockOutput())
    assert "key" not in sn
    assert list(iter(sn)) == []


def test_site_node_add_children_existing_key():
    p = Path("/fs")
    sn = site._PlanNode(p)
    c1 = MockOutput("s/1")
    c2 = MockOutput("s/2")
    sn.add_child("key", c1)
    sn.add_child("key", c2)
    assert len(list(iter(sn))) == 1
    assert list(iter(sn))[0].output == c1


@pytest.mark.parametrize(
    "outputs, dpaths, fpaths",
    [
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
    ],
)
def test_site_plan_ok(outputs, dpaths, fpaths):
    sp = site._Plan()
    for output in outputs:
        res = sp.add_output(MockOutput(output))
        assert res is None

    assert sorted([n.path for n in sp.dnodes()]) == (
        sorted([Path(dp) for dp in dpaths])
    )
    assert sorted([n.path for n in sp.fnodes()]) == (
        sorted([Path(fp) for fp in fpaths])
    )


@pytest.mark.parametrize(
    "output1, output2, exp_msg",
    [
        (
            "site/a",
            "site/a/b",
            "path of output item 'site/a/b' conflicts with 'site/a'",
        ),
    ],
)
def test_site_plan_fail(output1, output2, exp_msg):
    sp = site._Plan()
    sp.add_output(MockOutput(output1))
    with pytest.raises(ValueError, match=exp_msg):
        sp.add_output(MockOutput(output2))
