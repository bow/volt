"""Tests for volt._import."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pytest

from volt import error as err
from volt._import import import_file


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
