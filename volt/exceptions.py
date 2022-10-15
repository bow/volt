"""Custom exceptions."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

from typing import IO, Any, Optional

from click import ClickException

__all__ = [
    "VoltCliError",
    "VoltConfigError",
    "VoltError",
    "VoltResourceError",
]


class VoltError(Exception):

    """Base Volt exception class."""


class VoltCliError(VoltError, ClickException):

    """Exceptions displayed as error messages to users."""

    def show(self, file: Optional[IO[Any]] = None) -> None:
        from .utils import echo_err

        echo_err(self.format_message(), file=file)


class VoltConfigError(VoltCliError):

    """Raised for errors related to configuration values."""


class VoltResourceError(VoltConfigError):

    """Raised for errors when loading resources."""


class VoltMissingTemplateError(VoltResourceError):

    """Raised for errors when loading templates."""


VOLT_NO_PROJECT_ERR = VoltCliError("not in a volt project")
