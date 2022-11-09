"""Error handling and custom exceptions."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing import Any, IO, Optional

from click import ClickException
from structlog import get_logger

__all__ = [
    "VoltCliError",
    "VoltConfigError",
    "VoltError",
    "VoltMissingTemplateError",
    "VoltResourceError",
]


log = get_logger(__name__)


class VoltError(Exception):

    """Base Volt exception class."""


class VoltCliError(VoltError, ClickException):

    """Exceptions displayed as error messages to users."""

    def show(self, _: Optional[IO[Any]] = None) -> None:
        log.error(f"{self}")


class VoltConfigError(VoltCliError):

    """Raised for errors related to configuration values."""


class VoltResourceError(VoltConfigError):

    """Raised for errors when loading resources."""


class VoltMissingTemplateError(VoltResourceError):

    """Raised for errors when loading templates."""


class _VoltServerExit(SystemExit):

    """Raised to indicate the development server exiting."""

    def __init__(self, run_file_path: Path, *args: Any, **kwargs: Any) -> None:
        self.run_file_path = run_file_path
        super().__init__(*args, **kwargs)
