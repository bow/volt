# -*- coding: utf-8 -*-
"""
    Tests for volt.targets
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from pathlib import Path
from unittest.mock import call, create_autospec, patch

import pytest

from volt import exceptions as exc
from volt.targets import CopyTarget, PageTarget
from volt.units import Unit


def test_page_target():
    unit = create_autospec(
        Unit,
        spec_set=True,
        instance=True,
        metadata={"title": "test"},
    )
    path = create_autospec(Path, spec_set=True)
    contents = "foo"
    pt = PageTarget(unit, path, contents)

    assert pt.dest == path
    assert pt.metadata == {"title": "test"}

    res = pt.create()
    assert path.write_text.call_args_list == [call(contents)]
    assert res is None

    path.write_text.reset_mock()
    path.write_text.side_effect = OSError
    with pytest.raises(exc.VoltResourceError, match="could not write target"):
        pt.create()
    assert path.write_text.call_args_list == [call(contents)]


def test_copy_target():
    src = create_autospec(Path, spec_set=True)
    dest = create_autospec(Path, spec_set=True)
    ct = CopyTarget(src, dest)

    assert ct.dest == dest

    ct.dest.exists.return_value = False
    with patch("shutil.copy2") as copy2, patch("filecmp.cmp") as cmp:
        cmp.return_value = False
        res1 = ct.create()
        assert res1 is None
        assert copy2.call_count == 1
        assert cmp.call_count == 0

    ct.dest.exists.return_value = True
    with patch("shutil.copy2") as copy2, patch("filecmp.cmp") as cmp:
        cmp.return_value = False
        res2 = ct.create()
        assert res2 is None
        assert copy2.call_count == 1
        assert cmp.call_count == 1

    ct.dest.exists.return_value = True
    with patch("shutil.copy2") as copy2, patch("filecmp.cmp") as cmp:
        cmp.return_value = True
        res3 = ct.create()
        assert res3 is None
        assert copy2.call_count == 0
        assert cmp.call_count == 1
