"""Reusable import functions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import importlib.util as iutil
from os import PathLike
from types import ModuleType

from . import error as err


def import_file(fp: str | bytes | PathLike, mod_name: str) -> ModuleType:
    """Import the given file as the given module name"""

    spec = iutil.spec_from_file_location(mod_name, fp)
    if spec is None:
        raise err.VoltResourceError(f"not an importable file: {str(fp)}")

    mod = iutil.module_from_spec(spec)

    spec.loader.exec_module(mod)  # type: ignore

    return mod
