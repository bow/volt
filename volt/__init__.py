"""
    A minimal and extensible static website generator.

    :copyright: (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
    :license: BSD-3-Clause

"""
from pathlib import Path

from single_source import get_version

from .config import Config  # noqa: F401
from .engines import Engine, Markdown2Engine  # noqa: F401
from .site import Site  # noqa: F401
from .sources import FileSource, Markdown2Source, Source  # noqa: F401
from .targets import CopyTarget, FileTarget, Target, TemplateTarget  # noqa: F401
from .theme import Theme  # noqa: F401

NAME = "volt"

__author__ = "Wibowo Arindrarto"
__contact__ = "contact@arindrarto.dev"
__homepage__ = "https://github.com/bow/volt"
__version__ = get_version(__name__, Path(__file__).parent.parent)

del Path, get_version
