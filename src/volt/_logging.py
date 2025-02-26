"""Logging-related functionalities."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import io
import sys
import traceback
from dataclasses import dataclass
from functools import wraps
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Callable, Optional, ParamSpec, TypeVar, overload

import click
import structlog
from rich.console import Console
from rich.traceback import Traceback
from structlog.contextvars import bound_contextvars, merge_contextvars

from .config import _get_exc_style, _get_use_color


def style(text: str, **kwargs: Any) -> str:
    if not _get_use_color():
        return text
    return click.style(text=text, **kwargs)


T = TypeVar("T")
P = ParamSpec("P")


@overload
def log_method(__clb: Callable[P, T]) -> Callable[P, T]: ...


@overload
def log_method(*, with_args: bool) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def log_method(
    __clb: Optional[Callable[P, T]] = None,
    with_args: bool = False,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(clb: Callable[P, T]) -> Callable[P, T]:
        @wraps(clb)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            log = structlog.get_logger(clb.__module__)

            log_attrs: dict = {}
            if with_args:
                # Skip 'self' from being logged.
                if args_v := args[1:]:
                    log_attrs["args"] = args_v
                if kwargs:
                    log_attrs["kwargs"] = kwargs

            with bound_contextvars(**log_attrs):
                log.debug(f"calling method {clb.__qualname__}")

            rv = clb(*args, **kwargs)

            with bound_contextvars(**log_attrs):
                log.debug(f"returned from method {clb.__qualname__}")

            return rv

        return wrapped

    if __clb is None:
        return decorator
    return decorator(__clb)


@dataclass
class _LogLabel:
    bg: str
    text: str

    @property
    def styled(self) -> str:
        if _get_use_color():
            return style(f" {self.text} ", fg=self.bg, bold=True, reverse=True)
        return f"{self.text} |"


_level_styles = {
    "notset": _LogLabel(text="???", bg="white"),
    "debug": _LogLabel(text="DBG", bg="magenta"),
    "info": _LogLabel(text="INF", bg="cyan"),
    "warn": _LogLabel(text="WRN", bg="yellow"),
    "warning": _LogLabel(text="WRN", bg="yellow"),
    "error": _LogLabel(text="ERR", bg="red"),
    "critical": _LogLabel(text="CRT", bg="red"),
    "exception": _LogLabel(text="EXC", bg="red"),
}

_default_style = _level_styles["notset"]


class _ConsoleLogRenderer:
    def __call__(
        self,
        _logger: structlog.types.WrappedLogger,
        _name: str,
        event_dict: structlog.types.EventDict,
    ) -> str:
        level = event_dict.pop("level", "notset")
        label = _level_styles.get(level, _default_style)
        logstr = f"{label.styled} "

        event = f"{event_dict.pop('event', '')}" or "<no-event>"
        logstr += style(
            f"{event[0].upper() + event[1:]}",
            bold=level not in {"notset", "debug"},
        )

        exc_info = event_dict.pop("exc_info", None)
        logstr += self._render_event_dict(event_dict)
        logstr += self._render_exc_info(exc_info)

        return logstr

    @classmethod
    def _render_event_dict(cls, event_dict: structlog.types.EventDict) -> str:
        keys = event_dict.keys()
        if not keys:
            return ""

        rendered = " ·"
        for key in keys:
            value = cls._render_value(event_dict[key])
            rendered += style(f" {key}", fg="bright_black")
            rendered += style("=", fg="bright_white")
            rendered += style(value, fg="yellow")

        return rendered

    @staticmethod
    def _render_value(value: Any) -> str:
        str_value = ""
        match value:
            case str() | Path():
                str_value = f"{value}"
                if any(char.isspace() for char in str_value):
                    str_value = f"'{str_value}'"
            case bool():
                str_value = "yes" if value else "no"
            case _:
                str_value = repr(value)

        return str_value

    @staticmethod
    def _render_exc_info(exc_info: Any) -> str:
        if exc_info is None:
            return ""

        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()

        if all(item is None for item in exc_info):
            return ""

        rendered = "\n"
        match _get_exc_style():
            case "pretty":
                buf = io.StringIO()
                Console(file=buf).print(
                    Traceback.from_exception(
                        exc_type=exc_info[0],
                        exc_value=exc_info[1],
                        traceback=exc_info[2],
                        show_locals=True,
                        width=95,
                        suppress=[click],
                    )
                )
                rendered += buf.getvalue()
            case "plain":
                rendered += "".join(traceback.format_exception(*exc_info))
            case otherwise:
                raise ValueError(f"unexpected exception style: {otherwise!r}")

        return rendered.removesuffix("\n")


def init_logging(log_level: str) -> None:
    if structlog.is_configured():
        return None

    proc_chain: list[structlog.types.Processor] = [
        merge_contextvars,
        structlog.stdlib.add_log_level,
    ]

    log_level = log_level.upper()

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {
            "level": log_level,
            "handlers": ["err_console"],
        },
        "handlers": {
            "err_console": {
                "class": "logging.StreamHandler",
                "formatter": "console_formatter",
                "stream": "ext://sys.stderr",
            }
        },
        "formatters": {
            "console_formatter": {
                "()": "structlog.stdlib.ProcessorFormatter",
                "processor": _ConsoleLogRenderer(),
                "foreign_pre_chain": proc_chain,
            },
        },
        "loggers": {
            "asyncio": {
                "level": "WARNING",
            },
            "watchdog": {
                "level": "WARNING",
            },
        },
    }

    processors = proc_chain + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter]

    structlog.configure_once(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    dictConfig(log_config)
