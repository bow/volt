# -*- coding: utf-8 -*-
"""
    volt.server
    ~~~~~~~~~~~

    Development server.

"""
# (c) 2012-2021 Wibowo Arindrarto <contact@arindrarto.dev>

from datetime import datetime as dt
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, cast

from click import style

from . import __version__
from .config import SiteConfig
from .utils import echo_fmt


def make_server(sc: SiteConfig, host: str, port: int) -> Callable[[], None]:
    class HTTPRequestHandler(SimpleHTTPRequestHandler):

        server_version = f"volt-dev-server/{__version__}"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs["directory"] = f"{sc.out_path}"
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

            echo_fmt(fmt % (code, method, path))

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
        httpd.serve_forever()

    return serve
