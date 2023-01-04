"""Hooks for various events."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import sys
import structlog
from typing import Any

from . import signals as s


__all__ = [
    "log",
    "post_site_load_theme",
    "post_site_load_engines",
    "post_site_collect_targets",
    "pre_site_write",
    "post_site_write",
]


def name() -> str:
    """Return the name of the current hook.

    This function must be called inside the top-level hook function. That is, the
    function that is decorated with the hook.

    """
    frame = sys._getframe(1)
    hook_name = frame.f_code.co_name
    return hook_name


def log() -> Any:
    """Return a logger for a hook function.

    This function is meant to be called inside the top-level hook function. That is, the
    function that is decorated with the hook. Calling this elsewhere will result in the
    log message showing incorrect hook names.

    :returns: A :class:`structlog.BoundLogger` instance ready for logging.

    """
    frame = sys._getframe(1)
    hook_name = frame.f_code.co_name
    mod_name = frame.f_globals["__name__"]
    return structlog.get_logger(mod_name, hook=hook_name)


post_site_load_theme = s.post_site_load_theme.connect

post_site_load_engines = s.post_site_load_engines.connect

post_site_collect_targets = s.post_site_collect_targets.connect

pre_site_write = s.pre_site_write.connect
post_site_write = s.post_site_write.connect
