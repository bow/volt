# -*- coding: utf-8 -*-
"""
    volt.exceptions
    ~~~~~~~~~~~~~~~

    Custom exceptions.

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

from typing import Optional, TextIO

from click import ClickException, echo, style
from click._compat import get_text_stderr

__all__ = [
    "VoltCliError",
    "VoltConfigError",
    "VoltError",
    "VoltResourceError",
    "VoltTimezoneError",
]


class VoltError(Exception):

    """Base Volt exception class."""


class VoltCliError(VoltError, ClickException):

    """Exceptions displayed as error messages to users."""

    def show(self, file: Optional[TextIO] = None) -> None:
        if file is None:
            file = get_text_stderr()
        echo(
            f"{style(' Error ', bg='red')}"
            f" {self.format_message()}",
            file=file,
        )


class VoltConfigError(VoltCliError):

    """Raised for errors related to configuration values."""


class VoltResourceError(VoltConfigError):

    """Raised for errors when loading resources."""


class VoltTimezoneError(VoltConfigError):

    """Raised for timezone object creation errors."""

    def __init__(self, tzname: str) -> None:
        super().__init__(f"timezone {tzname!r} is invalid")
