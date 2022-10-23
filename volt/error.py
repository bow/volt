"""Error handling and custom exceptions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

from typing import IO, Any, Optional

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

    def show(self, file: Optional[IO[Any]] = None) -> None:
        log.error(f"{self}")


class VoltConfigError(VoltCliError):

    """Raised for errors related to configuration values."""


class VoltResourceError(VoltConfigError):

    """Raised for errors when loading resources."""


class VoltMissingTemplateError(VoltResourceError):

    """Raised for errors when loading templates."""
