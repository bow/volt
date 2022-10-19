"""
    A versatile static website generator.

    :copyright: (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>
    :license: BSD

"""
from pathlib import Path

from single_source import get_version

from .config import Config  # noqa: F401
from .engines import Engine  # noqa: F401
from .sources import MarkdownSource  # noqa: F401
from .targets import Target, TemplateTarget, CopyTarget  # noqa: F401

NAME = "volt"

__author__ = "Wibowo Arindrarto"
__contact__ = "contact@arindrarto.dev"
__homepage__ = "https://github.com/bow/volt"
__version__ = get_version(__name__, Path(__file__).parent.parent)

del Path, get_version
