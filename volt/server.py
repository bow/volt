"""Development server."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import queue
import signal
import sys
import threading
from contextlib import suppress
from datetime import datetime as dt
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast, Any, Callable, NoReturn, Optional

import structlog
from click import echo
from click._compat import get_text_stderr
from structlog.contextvars import bound_contextvars
from watchdog import events
from watchdog.observers import Observer

from . import __version__, constants
from .config import Config
from .error import _VoltServerExit
from ._logging import style


__all__ = ["make_server"]


log = structlog.get_logger(__name__)


class _RunFile:
    @classmethod
    def from_config(cls, config: Config) -> "_RunFile":
        log.debug("creating server run file object from config")
        return cls(config._server_run_path, config.with_drafts)

    @classmethod
    def from_path(cls, path: Path) -> Optional["_RunFile"]:
        with bound_contextvars(path=path):
            log.debug("creating server run file object from existing file")
            if not path.exists():
                log.debug("no server run file found")
                return None

        drafts = path.read_text().strip() == "drafts"
        return cls(path, drafts)

    def __init__(self, path: Path, drafts: bool) -> None:
        self._path = path
        self._drafts = drafts

    @property
    def path(self) -> Path:
        return self._path

    @property
    def drafts(self) -> bool:
        return self._drafts

    def set_drafts(self) -> None:
        self._drafts = True

    def unset_drafts(self) -> None:
        self._drafts = False

    def dump(self) -> None:
        log.debug(
            "writing server run file",
            path=self.path,
            drafts="on" if self.drafts else "off",
        )
        self.path.write_text("drafts" if self._drafts else "no-drafts")
        return None

    def remove(self) -> None:
        log.debug("removing server run file", path=self.path)
        with suppress(OSError):
            self.path.unlink()


def make_server(config: Config, host: str, port: int) -> Callable[[], None]:
    class HTTPRequestHandler(SimpleHTTPRequestHandler):

        server_version = f"volt-dev-server/{__version__}"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs["directory"] = f"{config.target_dir}"
            super().__init__(*args, **kwargs)

        def log_message(self, fmt: str, *args: Any) -> None:
            # overrides parent log_message to provide a more compact output.
            method: str = args[0]
            status: HTTPStatus = args[1]
            path: str = args[2]

            code = f"{status.value}"
            if status.value >= 400:
                code = style(code, fg="red", bold=True)
            elif status.value >= 300:
                code = style(code, fg="yellow", bold=True)
            else:
                code = style(code, fg="cyan", bold=True)

            path = style(path, fg="bright_blue")

            echo(fmt % (code, method, path), file=get_text_stderr())

        def log_request(
            self,
            code: str | int = "-",
            size: str | int = "-",
        ) -> Any:
            ts = dt.now().strftime("%H:%M:%S.%f")
            fmt = '%30s | %%s · %%s "%%s"' % style(ts, fg="bright_black")
            method, path = self.requestline[:-9].split(" ", 1)
            self.log_message(fmt, method, cast(HTTPStatus, code), path)

        def log_error(self, *args: Any) -> None:
            # overrides parent log_error to reduce noise.
            pass

    run_file = _RunFile.from_config(config)
    run_file.dump()

    def serve() -> None:
        httpd = ThreadingHTTPServer((host, port), HTTPRequestHandler)

        def signal_handler(signum: int, frame: Any) -> NoReturn:
            try:
                httpd.server_close()
            finally:
                if signum == signal.SIGINT:
                    print("", file=sys.stderr, flush=True)
                log.info(f"dev server stopped ({signal.strsignal(signum)})")
                raise _VoltServerExit(run_file_path=run_file.path)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        log.info("dev server listening", addr=f"http://{host}:{port}")
        httpd.serve_forever()

    return serve


class _SyncQueue(queue.Queue):

    """A queue of size=1 that drops events sent to it while it processes tasks"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["maxsize"] = 1
        super().__init__(*args, **kwargs)
        self._putlock = threading.Lock()

    def put(
        self,
        item: Any,
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:

        if not self._putlock.acquire(blocking=False):
            return

        if self.unfinished_tasks > 0:
            self._putlock.release()
            return

        with suppress(queue.Full):
            super().put(item, False, timeout=None)

        self._putlock.release()


class _BuildObserver(Observer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._event_queue = _SyncQueue()


class _BuildHandler(events.RegexMatchingEventHandler):
    def __init__(self, config: Config, build_func: Callable) -> None:

        prefix = f"{config.project_dir_rel}".replace(".", r"\.")
        regexes = [
            *[
                f"^{prefix + '/' + dirname + '/'}.+$"
                for dirname in (
                    constants.PROJECT_EXTENSION_DIRNAME,
                    constants.PROJECT_SOURCES_DIRNAME,
                    constants.PROJECT_STATIC_DIRNAME,
                    constants.SITE_THEMES_DIRNAME,
                )
            ],
            f"^{prefix + '/' + constants.CONFIG_FNAME}$",
            f"^{prefix + '/' + constants.SERVER_RUN_FNAME}$",
        ]
        ignore_regexes = [
            f"^{prefix + '/' + constants.PROJECT_TARGET_DIRNAME + '/'}.+$",
            f"^{prefix + '/__pycache__'}.+",
        ]
        super().__init__(regexes, ignore_regexes, case_sensitive=True)
        self.config = config
        self._build = build_func

    def on_any_event(self, event: Any) -> None:

        log_attrs: dict = {}
        match type(event):

            case events.FileCreatedEvent:
                log_attrs = dict(
                    reason="file_created",
                    file=event.src_path,
                )

            case events.FileModifiedEvent:
                log_attrs = dict(
                    reason="file_modified",
                    file=event.src_path,
                )

            case events.FileDeletedEvent:
                log_attrs = dict(
                    reason="file_deleted",
                    file=event.src_path,
                )

            case events.FileMovedEvent:
                log_attrs = dict(
                    reason="file_moved",
                    src=event.src_path,
                    dest=event.dest_path,
                )

            case events.DirCreatedEvent:
                log_attrs = dict(
                    reason="dir_created",
                    dir=event.src_path,
                )

            case events.DirModifiedEvent:
                log_attrs = dict(
                    reason="dir_modified",
                    dir=event.src_path,
                )

            case events.DirDeletedEvent:
                log_attrs = dict(
                    reason="dir_deleted",
                    dir=event.src_path,
                )

            case events.DirMovedEvent:
                log_attrs = dict(
                    reason="dir_moved",
                    src=event.src_path,
                    dest=event.dest_path,
                )

            case _:
                log_attrs = dict(reason="unknown")

        log.info("rebuilding site", **log_attrs)
        self._build()
        return None


class _Rebuilder:
    def __init__(self, config: Config, build_func: Callable) -> None:
        self._observer = _BuildObserver()
        self._observer.schedule(
            _BuildHandler(config, build_func),
            config.project_dir_rel,
            recursive=True,
        )

    def __enter__(self):  # type: ignore
        return self._observer.start()

    def __exit__(self, typ, value, traceback):  # type: ignore
        self._observer.stop()
        self._observer.join()
