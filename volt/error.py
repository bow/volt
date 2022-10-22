"""Error handling and custom exceptions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import sys
from typing import NoReturn

from click import ClickException
from structlog import get_logger

__all__ = [
    "VoltCliError",
    "VoltConfigError",
    "VoltError",
    "VoltResourceError",
]


log = get_logger(__name__)


class VoltError(Exception):

    """Base Volt exception class."""


class VoltCliError(VoltError, ClickException):

    """Exceptions displayed as error messages to users."""


class VoltConfigError(VoltCliError):

    """Raised for errors related to configuration values."""


class VoltResourceError(VoltConfigError):

    """Raised for errors when loading resources."""


class VoltMissingTemplateError(VoltResourceError):

    """Raised for errors when loading templates."""


def halt(reason: str, exit_code: int = 1) -> NoReturn:
    log.error("halting execution", reason=reason)
    sys.exit(exit_code)


def halt_not_in_project() -> NoReturn:
    halt("not-in-volt-project-dir")
