"""Development server."""
# (c) 2012-2021 Wibowo Arindrarto <contact@arindrarto.dev>

import queue
import threading
from contextlib import suppress
from datetime import datetime as dt
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Optional, cast

from click import style
from watchdog import events
from watchdog.observers import Observer

from . import __version__, constants
from .config import Config
from .utils import echo_fmt, echo_info


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
                code = style(code, fg="blue", bold=True)
            else:
                code = style(code, fg="green", bold=True)

            echo_fmt(fmt % (code, method, path), capitalize=False)

        def log_request(
            self,
            code: str | int = "-",
            size: str | int = "-",
        ) -> Any:
            ts = dt.now().strftime("%H:%M:%S.%f")
            fmt = '%29s | %%s · %%s "%%s"' % style(ts, fg="bright_black")
            method, path = self.requestline[:-9].split(" ", 1)
            self.log_message(fmt, method, cast(HTTPStatus, code), path)

        def log_error(self, *args: Any) -> None:
            # overrides parent log_error to reduce noise.
            pass

    def serve() -> None:
        httpd = ThreadingHTTPServer((host, port), HTTPRequestHandler)
        echo_info(f"dev server listening at http://{host}:{port}")
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

        msg = ""
        match type(event):

            case events.FileCreatedEvent:
                msg = f"file created: {event.src_path}"

            case events.FileModifiedEvent:
                msg = f"file modified: {event.src_path}"

            case events.FileDeletedEvent:
                msg = f"file deleted: {event.src_path}"

            case events.FileMovedEvent:
                msg = f"file moved: {event.src_path} to {event.dest_path}"

            case events.DirCreatedEvent:
                msg = f"directory created: {event.src_path}"

            case events.DirModifiedEvent:
                msg = f"directory modified: {event.src_path}"

            case events.DirDeletedEvent:
                msg = f"directory deleted: {event.src_path}"

            case events.DirMovedEvent:
                msg = f"directory moved: {event.src_path} to {event.dest_path}"

            case _:
                msg = "unknown change detected"

        echo_info(f"{msg} -- rebuilding")
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
