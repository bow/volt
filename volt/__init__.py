"""
    A minimal and extensible static website generator.

    :copyright: (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
    :license: BSD-3-Clause

"""

from pathlib import Path
from importlib.metadata import version


from .config import Config  # noqa: F401
from .engines import Engine, MarkdownEngine  # noqa: F401
from .outputs import CopyOutput, FileOutput, Output, TemplateOutput  # noqa: F401
from .site import Site  # noqa: F401
from .theme import Theme  # noqa: F401

NAME = "volt"

__author__ = "Wibowo Arindrarto"
__contact__ = "contact@arindrarto.dev"
__homepage__ = "https://github.com/bow/volt"
__version__ = version(__name__)

del Path, version
