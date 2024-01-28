"""Development server."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import queue
import signal
import sys
import socket
import threading
import time
from contextlib import suppress
from datetime import datetime as dt
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast, Any, Callable, NoReturn, Optional, Self
from webbrowser import open as open_browser

import structlog
from blinker import signal as blinker_signal
from click import echo
from click._compat import get_text_stderr
from structlog.contextvars import bound_contextvars
from watchdog import events
from watchdog.observers import Observer

from . import __version__, constants, signals as blinker_signals
from .config import Config
from .error import _VoltServerExit
from ._logging import style


__all__ = ["make_server"]


log = structlog.get_logger(__name__)


_pre_server_serve = blinker_signal("_pre_server_serve")


class _RunFile:
    DRAFT_ON = "draft"
    DRAFT_OFF = "no-draft"

    @classmethod
    def from_config(cls, config: Config, draft: bool) -> Self:
        log.debug("creating server run file object from config", draft=draft)
        return cls(path=config._server_run_path, draft=draft)

    @classmethod
    def from_path(cls, path: Path) -> Optional[Self]:
        with bound_contextvars(path=path):
            log.debug("creating server run file object from existing file")
            if not path.exists():
                log.debug("no server run file found")
                return None

        draft = path.read_text().strip() == cls.DRAFT_ON
        return cls(path, draft)

    def __init__(self, path: Path, draft: bool) -> None:
        self._path = path
        self._draft = draft

    @property
    def path(self) -> Path:
        return self._path

    @property
    def draft(self) -> bool:
        return self._draft

    def toggle_draft(self, value: Optional[bool]) -> Self:
        log.debug("toggling server draft mode", value=value)
        new_value = value if value is not None else (not self._draft)
        self._draft = new_value
        log.debug("toggled server draft mode", value=self.draft)
        return self

    def dump(self) -> None:
        log.debug("writing server run file", path=self.path, draft=self.draft)
        self.path.write_text(self.DRAFT_ON if self.draft else self.DRAFT_OFF)
        return None

    def remove(self) -> None:
        log.debug("removing server run file", path=self.path)
        with suppress(OSError):
            self.path.unlink()


def make_server(
    config: Config,
    host: str,
    port: int,
    with_draft: bool,
    with_sig_handlers: bool,
    log_level: str,
    log_color: bool,
) -> Callable[[bool], None]:
    class HTTPRequestHandler(SimpleHTTPRequestHandler):
        server_version = f"volt-dev-server/{__version__}"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs["directory"] = f"{config.output_dir}"
            super().__init__(*args, **kwargs)

        if log_level in {"warning", "error", "critical"}:

            def log_message(self, fmt: str, *args: Any) -> None:
                return None

        else:

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
            if log_color:
                fmt = '%30s | %%s · %%s "%%s"' % style(ts, fg="bright_black")
            else:
                fmt = '%21s - %%s · %%s "%%s"' % style(ts, fg="bright_black")
            method, path = self.requestline[:-9].split(" ", 1)
            self.log_message(fmt, method, cast(HTTPStatus, code), path)

        def log_error(self, *args: Any) -> None:
            # overrides parent log_error to reduce noise.
            pass

    run_file = _RunFile.from_config(config, with_draft)
    run_file.dump()

    def serve(with_open_browser: bool) -> None:
        httpd = ThreadingHTTPServer((host, port), HTTPRequestHandler)

        if with_sig_handlers:

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

        blinker_signals.send(
            _pre_server_serve,
            with_open_browser=with_open_browser,
            host=host,
            port=port,
        )
        log.info("dev server listening", url=f"http://{host}:{port}")
        httpd.serve_forever()

    return serve


_browser_opened = False


@_pre_server_serve.connect
def _open_browser_handler(
    _: Any,
    with_open_browser: bool,
    host: str,
    port: int,
) -> None:
    if not with_open_browser:
        return None

    global _browser_opened

    if _browser_opened:
        return None

    if _wait_ready(host, port):
        log.debug("opening browser", host=host, port=port)
        open_browser(f"http://{host}:{port}")
        _browser_opened = True

    return None


def _wait_ready(
    host: str,
    port: int,
    max_attempts: int = 10,
    wait_per_attempt: float = 0.1,
) -> bool:
    with bound_contextvars(host=host, port=port):
        log.debug("checking if server is ready")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        num_attempts = 0
        while num_attempts < max_attempts:
            num_attempts += 1
            try:
                s.connect((host, port))
                s.close()
                log.debug("server is ready")
                return True
            except OSError:
                log.debug("waiting for server to be ready", num_attempts=num_attempts)
                time.sleep(wait_per_attempt)

    return False


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
        super().__init__(*args, **kwargs)  # type: ignore[no-untyped-call]
        self._event_queue = _SyncQueue()


class _BuildHandler(events.RegexMatchingEventHandler):
    def __init__(self, config: Config, build_func: Callable) -> None:
        prefix = f"{config.project_dir_rel}".replace(".", r"\.")
        regexes = [
            *[
                f"^{prefix + '/' + dir_name + '/'}.+$"
                for dir_name in (
                    constants.PROJECT_EXTENSION_DIR_NAME,
                    constants.PROJECT_CONTENTS_DIR_NAME,
                    (
                        f"{constants.PROJECT_CONTENTS_DIR_NAME}"
                        f"/{constants.PROJECT_STATIC_DIR_NAME}"
                    ),
                    constants.SITE_THEMES_DIR_NAME,
                )
            ],
            f"^{prefix + '/' + constants.CONFIG_FILE_NAME}$",
            f"^{prefix + '/' + constants.SERVER_RUN_FILE_NAME}$",
        ]
        ignore_regexes = [
            f"^{prefix + '/' + constants.PROJECT_OUTPUT_DIR_NAME + '/'}.+$",
            ".*__pycache__.*",
        ]
        super().__init__(
            regexes,
            ignore_regexes,
            case_sensitive=True,
        )  # type: ignore[no-untyped-call]
        self.config = config
        self._build = build_func

    def on_any_event(self, event: Any) -> None:
        log_attrs: dict = {}
        match type(event):
            case events.FileCreatedEvent:
                log_attrs = dict(
                    reason="file_created",
                    file=event.src_path.removeprefix("./"),
                )

            case events.FileModifiedEvent:
                log_attrs = dict(
                    reason="file_modified",
                    file=event.src_path.removeprefix("./"),
                )

            case events.FileDeletedEvent:
                log_attrs = dict(
                    reason="file_deleted",
                    file=event.src_path.removeprefix("./"),
                )

            case events.FileMovedEvent:
                log_attrs = dict(
                    reason="file_moved",
                    src=event.src_path.removeprefix("./"),
                    dest=event.dest_path.removeprefix("./"),
                )

            case events.DirCreatedEvent:
                log_attrs = dict(
                    reason="dir_created",
                    dir=event.src_path.removeprefix("./"),
                )

            case events.DirModifiedEvent:
                log_attrs = dict(
                    reason="dir_modified",
                    dir=event.src_path.removeprefix("./"),
                )

            case events.DirDeletedEvent:
                log_attrs = dict(
                    reason="dir_deleted",
                    dir=event.src_path.removeprefix("./"),
                )

            case events.DirMovedEvent:
                log_attrs = dict(
                    reason="dir_moved",
                    src=event.src_path.removeprefix("./"),
                    dest=event.dest_path.removeprefix("./"),
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
        )  # type: ignore[no-untyped-call]

    def __enter__(self):  # type: ignore
        return self._observer.start()

    def __exit__(self, typ, value, traceback):  # type: ignore
        self._observer.stop()
        self._observer.join()
