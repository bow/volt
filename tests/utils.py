"""Volt test utilities."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import socket
import time
from contextlib import closing, contextmanager, AbstractContextManager as ACM
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Generator, Optional

import pytest
import tomlkit
from click.testing import CliRunner

from volt import cli
from volt.constants import PROJECT_TARGET_DIR_NAME


# Layout for test files and directories.
DirLayout = dict[Path | str, str | bytes | Optional["DirLayout"]]


class CommandRunner(CliRunner):
    @contextmanager
    def isolated_filesystem(  # type: ignore[override]
        self,
        layout: Optional[DirLayout] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Generator[Path, None, None]:
        with super().isolated_filesystem(*args, **kwargs) as fs:
            root = Path(fs)
            self._create_files(root, layout)
            yield root

    def _create_files(self, root: Path, layout: Optional[DirLayout]) -> None:

        if layout is None:
            return None

        cur_dir = root
        nodes = [(cur_dir / k, v) for k, v in layout.items()]
        while nodes:
            cur_p, cur_contents = nodes.pop()

            if isinstance(cur_contents, dict):
                cur_p.mkdir(parents=True, exist_ok=True)
                nodes.extend([(cur_p / k, v) for k, v in cur_contents.items()])
                continue

            cur_p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(cur_contents, str):
                cur_p.write_text(cur_contents)
            elif isinstance(cur_contents, bytes):
                cur_p.write_bytes(cur_contents)
            elif cur_contents is None:
                cur_p.touch()

        return None


def assert_dir_empty(path: Path) -> None:
    assert path.is_dir()
    contents = list(path.iterdir())
    assert contents == [], contents


def assert_dir_contains_only(path: Path, fps: list[str] | list[Path]) -> None:
    assert path.is_dir()
    contents = sorted(path.iterdir())
    assert contents == sorted(
        [Path(fp) if Path(fp).is_absolute() else (path / fp) for fp in fps]
    ), contents


def load_config(config_fp: Path) -> dict:
    with config_fp.open() as src:
        config = tomlkit.load(src)
    return config


def load_project_config(project_dir: Path) -> dict:
    return load_config(project_dir / "volt.toml")


def assert_keys_only(d: dict, keys: list[Any]) -> None:
    ks = d.keys()
    assert sorted(ks) == sorted(keys), ks


_sentinel = object()


def has_and_pop(d: dict, key: Any) -> bool:
    try:
        return d.pop(key, _sentinel) is not _sentinel
    except KeyError:
        return False


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_until_exists(fp: Path, timeout: float = 5.0, freq: float = 0.2) -> bool:

    waited = 0.0
    while not fp.exists():
        time.sleep(freq)
        waited += freq
        if waited > timeout:
            return False

    return True


def invoke_isolated_server(
    isolation_func: Callable[[Path, str], ACM[Path]],
    project_fixture_name: str,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    args: Optional[list[str]] = None,
    startup_timeout: float = 5.0,
    startup_check_freq: float = 0.2,
    sentinel_project_file: Path = Path(PROJECT_TARGET_DIR_NAME) / "index.html",
) -> Path:

    port = port or find_free_port()
    sentinel_file: Optional[Path] = None
    project_dir: Optional[Path] = None

    def serve() -> None:
        nonlocal sentinel_file, project_dir

        runner = CommandRunner()
        toks = args or ["serve", "-h", host, "-p", f"{port}", "--no-sig-handlers"]

        with runner.isolated_filesystem() as ifs:

            with isolation_func(ifs, project_fixture_name) as pd:

                project_dir = pd
                sentinel_file = pd / sentinel_project_file
                assert not sentinel_file.exists()

                runner.invoke(cli.root, toks)

    def start() -> None:
        nonlocal sentinel_file

        thread = Thread(target=serve)
        thread.daemon = True
        thread.start()

        waited = 0.0
        while sentinel_file is None or not sentinel_file.exists():
            time.sleep(startup_check_freq)
            waited += startup_check_freq
            if waited > startup_timeout:
                pytest.fail(
                    f"expected built result file {sentinel_file} still nonexistent"
                    f" after waiting for {waited:.1f}s"
                )

    start()

    if project_dir is None:
        pytest.fail("failed to set isolated project directory")

    return project_dir
