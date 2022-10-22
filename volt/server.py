"""Development server."""
# (c) 2012-2021 Wibowo Arindrarto <contact@arindrarto.dev>

import queue
import signal
import sys
import threading
from contextlib import suppress
from datetime import datetime as dt
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, NoReturn, Optional, cast

import structlog
from click import echo, style
from click._compat import get_text_stderr
from watchdog import events
from watchdog.observers import Observer

from . import __version__, constants
from .config import Config


log = structlog.get_logger(__name__)


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

            path = style(path, fg="magenta")

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

    def serve() -> None:
        httpd = ThreadingHTTPServer((host, port), HTTPRequestHandler)

        def signal_handler(signum: int, frame: Any) -> NoReturn:
            try:
                httpd.server_close()
            finally:
                if signum == signal.SIGINT:
                    print("", file=sys.stderr, flush=True)
                log.info(f"dev server stopped ({signal.strsignal(signum)})")
                sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        log.info("dev server listening", addr=f"http://{host}:{port}")
        httpd.serve_forever()

    return serve


class SyncQueue(queue.Queue):

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


class BuildObserver(Observer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._event_queue = SyncQueue()


class BuildHandler(events.RegexMatchingEventHandler):
    def __init__(self, config: Config, build_func: Callable) -> None:

        prefix = f"{config.project_dir_rel}".replace(".", r"\.")
        regexes = [
            *[
                f"^{prefix + '/' + dirname + '/'}.+$"
                for dirname in (
                    constants.SITE_EXTENSION_DIRNAME,
                    constants.SITE_SOURCES_DIRNAME,
                    constants.SITE_STATIC_DIRNAME,
                    constants.SITE_THEMES_DIRNAME,
                )
            ],
            f"^{prefix + '/' + constants.CONFIG_FNAME}$",
        ]
        ignore_regexes = [
            f"^{prefix + '/' + constants.SITE_TARGET_DIRNAME + '/'}.+$",
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
                    reason="file-created",
                    file=event.src_path,
                )

            case events.FileModifiedEvent:
                log_attrs = dict(
                    reason="file-modified",
                    file=event.src_path,
                )

            case events.FileDeletedEvent:
                log_attrs = dict(
                    reason="file-deleted",
                    file=event.src_path,
                )

            case events.FileMovedEvent:
                log_attrs = dict(
                    reason="file-moved",
                    src=event.src_path,
                    dest=event.dest_path,
                )

            case events.DirCreatedEvent:
                log_attrs = dict(
                    reason="dir-created",
                    dir=event.src_path,
                )

            case events.DirModifiedEvent:
                log_attrs = dict(
                    reason="dir-modified",
                    dir=event.src_path,
                )

            case events.DirDeletedEvent:
                log_attrs = dict(
                    reason="dir-deleted",
                    dir=event.src_path,
                )

            case events.DirMovedEvent:
                log_attrs = dict(
                    reason="dir-moved",
                    src=event.src_path,
                    dest=event.dest_path,
                )

            case _:
                log_attrs = dict(reason="unknown")

        log.info("rebuilding site", **log_attrs)
        self._build()
        return None


class Rebuilder:
    def __init__(self, config: Config, build_func: Callable) -> None:
        self._observer = BuildObserver()
        self._observer.schedule(
            BuildHandler(config, build_func),
            config.project_dir_rel,
            recursive=True,
        )

    def __enter__(self):  # type: ignore
        return self._observer.start()

    def __exit__(self, typ, value, traceback):  # type: ignore
        self._observer.stop()
        self._observer.join()
