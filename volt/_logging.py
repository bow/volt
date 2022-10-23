"""Logging-related functionalities."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import os
import sys
import traceback
from dataclasses import dataclass
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Optional

import better_exceptions
import structlog
from click import style as cstyle
from structlog.contextvars import bind_contextvars, merge_contextvars

from .config import _get_exc_style, _get_use_color


def style(text: str, **kwargs: Any) -> str:
    if not _get_use_color():
        return text
    return cstyle(text=text, **kwargs)


def _get_exceptions_max_length(default: int = 65) -> Optional[int]:
    value = os.environ.get("VOLT_EXCEPTIONS_MAX_LENGTH", None)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


better_exceptions.MAX_LENGTH = _get_exceptions_max_length()


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
        logstr += style(f"{event[0].upper() + event[1:]}", bold=True)

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
                rendered += "".join(better_exceptions.format_exception(*exc_info))
            case "plain":
                rendered += "".join(traceback.format_exception(*exc_info))

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
    }

    processors = proc_chain + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter]

    structlog.configure_once(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    dictConfig(log_config)

    if log_level == "DEBUG":
        from platform import platform
        from . import __version__

        bind_contextvars(
            python_version=sys.version,
            volt_version=__version__,
            platform=platform(),
        )
