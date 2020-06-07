# -*- coding: utf-8 -*-
"""
    Volt test utilities.
    ~~~~~~~~~~~~~~~~~~~~

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>


def create_fs_fixture(fs, layout):
    for dname in layout["dirs"]:
        fs.joinpath(dname).mkdir()
    for fname, contents in layout["files"].items():
        fp = fs.joinpath(fname)
        fp.parent.mkdir(parents=True, exist_ok=True)
        with fp.open(mode="w") as fh:
            fh.write(contents)
