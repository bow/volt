"""Signals for hooks."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

import structlog
from blinker import signal, NamedSignal
from structlog.contextvars import bound_contextvars


log = structlog.get_logger(__name__)


post_site_load_engines = signal("post_site_load_engines")
post_site_collect_targets = signal("post_site_collect_targets")
pre_site_write = signal("pre_site_write")


def send(signal: NamedSignal, *args: Any, **kwargs: Any) -> None:
    with bound_contextvars(signal=f"{signal.name}"):
        log.debug("sending to signal")
        rvs = signal.send(*args, **kwargs)
        log.debug("sent to signal", num_receiver=len(rvs))
    return None


def _clear() -> None:
    for s in (
        post_site_load_engines,
        post_site_collect_targets,
        pre_site_write,
    ):
        log.debug("clearing receivers", signal=s.name)
        s.receivers.clear()
    return None
