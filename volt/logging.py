"""Logging-related functionalities."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import sys
from dataclasses import dataclass
from logging.config import dictConfig
from pathlib import Path

import better_exceptions
import structlog
from click import style


@dataclass
class _LogLabel:

    bg: str
    text: str

    @property
    def styled(self) -> str:
        return style(f" {self.text} ", fg=self.bg, bold=True, reverse=True)


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

        event = event_dict.pop("event", "")
        if isinstance(event, Exception):
            event = f"{event.__class__.__name__}: {event}"
        else:
            event = f"{event}"
        logstr += style(f"{event[0].upper() + event[1:]}", bold=True)

        exc_info = event_dict.pop("exc_info", None)

        if event_dict.keys():
            logstr += " ·"

        for key in event_dict.keys():
            value = event_dict[key]
            if not isinstance(value, (str, Path)):
                value = repr(value)
            else:
                value = f"{value}"
            logstr += style(f" {key}", fg="bright_black")
            logstr += style("=", fg="bright_white")
            logstr += style(f"{value}", fg="yellow")

        if exc_info is not None:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
            logstr += "\n"
            logstr += "".join(better_exceptions.format_exception(*exc_info))

        return logstr


def init_logging(log_level: str) -> None:
    proc_chain: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
    ]

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {
            "level": log_level.upper(),
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
