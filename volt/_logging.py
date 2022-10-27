"""Logging-related functionalities."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import io
import sys
import traceback
from dataclasses import dataclass
from functools import wraps
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Callable, TypeVar, ParamSpec

import click
import structlog
from rich.console import Console
from rich.traceback import Traceback
from structlog.contextvars import bind_contextvars, merge_contextvars

from .config import _get_exc_style, _get_use_color


T = TypeVar("T")
P = ParamSpec("P")


def style(text: str, **kwargs: Any) -> str:
    if not _get_use_color():
        return text
    return click.style(text=text, **kwargs)


def log_method(clb: Callable[P, T]) -> Callable[P, T]:
    @wraps(clb)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        log = structlog.get_logger(clb.__module__)
        log.debug(f"calling method {clb.__qualname__}")
        rv = clb(*args, **kwargs)
        log.debug(f"returned from method {clb.__qualname__}")

        return rv

    return wrapped


@dataclass
class _LogLabel:

    bg: str
    text: str

    @property
    def styled(self) -> str:
        if _get_use_color():
            return style(f" {self.text} ", fg=self.bg, bold=True, reverse=True)
        return f"◆ {self.text} |"


_level_styles = {
    "notset": _LogLabel(text="???", bg="white"),
    "debug": _LogLabel(text="DBG", bg="magenta"),
    "info": _LogLabel(text="INF", bg="cyan"),
    "warn": _LogLabel(text="WRN", bg="yellow"),
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

        event = f"{event_dict.pop('event', '')}"
        logstr += style(
            f"{event[0].upper() + event[1:]}",
            bold=level not in {"notset", "debug"},
        )

        exc_info = event_dict.pop("exc_info", None)
        logstr += self._render_event_dict(event_dict)
        logstr += self._render_exc_info(exc_info)

        return logstr

    @staticmethod
    def _render_event_dict(event_dict: structlog.types.EventDict) -> str:

        keys = event_dict.keys()
        if not keys:
            return ""

        rendered = " ·"
        for key in event_dict.keys():
            value = event_dict[key]
            if not isinstance(value, (str, Path)):
                if isinstance(value, bool):
                    value = "yes" if value else "no"
                else:
                    value = repr(value)
            else:
                value = f"{value}"
                if any(char.isspace() for char in value):
                    value = f"'{value}'"
            rendered += style(f" {key}", fg="bright_black")
            rendered += style("=", fg="bright_white")
            rendered += style(f"{value}", fg="yellow")

        return rendered

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


def bind_drafts_context(drafts: bool) -> None:
    if not drafts:
        return None
    bind_contextvars(drafts=True)
    return None


def init_logging(log_level: str) -> None:
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
            }
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
