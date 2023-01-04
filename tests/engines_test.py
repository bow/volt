"""Tests for volt.engines."""
# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from volt import constants
from volt.config import Config
from volt.error import VoltConfigError
from volt.engines import EngineSpec, StaticEngine
from volt.engines.common import _calc_relpath
from volt.theme import Theme


def test_engine_spec_load_ok_module(mocker: MockerFixture) -> None:
    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    spec = EngineSpec(
        id="mock",
        config=m_config,
        theme=m_theme,
        source="static",
        opts={"foo": 1},
        module="volt.engines:StaticEngine",
        klass=None,
    )

    engine = spec.load()
    assert isinstance(engine, StaticEngine)
    assert engine.id == "mock"
    assert engine.opts == {"foo": 1}
    assert engine.source_dir_name == "static"
    assert engine.config is m_config
    assert engine.theme is m_theme


def test_engine_spec_load_ok_class(
    tmp_path: Path,
    isolated_project_dir: Callable,
) -> None:

    with isolated_project_dir(tmp_path, "ok_extended") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        theme = Theme.from_config(config)

        spec = EngineSpec(
            id="gallery",
            config=config,
            theme=theme,
            source="gallery",
            opts={"foo": 1},
            module=None,
            klass="GalleryEngine",
        )

        engine = spec.load()
        assert engine.__class__.__name__ == "GalleryEngine"
        assert engine.id == "gallery"
        assert engine.opts == {"foo": 1}
        assert engine.source_dir_name == "gallery"
        assert engine.config is config
        assert engine.theme is theme


def test_engine_spec_init_err_all_nones(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(
        VoltConfigError, match="one of 'module' or 'class' must be a valid string value"
    ):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module=None,
            klass=None,
        )


def test_engine_spec_init_err_all_defined(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(
        VoltConfigError, match="only one of 'module' or 'class' may be specified"
    ):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module="GalleryEngine",
            klass="volt.engines:StaticEngine",
        )


def test_engine_spec_init_err_invalid_specifier_module(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(VoltConfigError, match="invalid engine class specifier"):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module="volt.engines.StaticEngine",
            klass=None,
        )


def test_engine_spec_init_err_missing_module(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(VoltConfigError, match="not a valid module: foo.bar"):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module="foo.bar:BzztEngine",
            klass=None,
        )


def test_engine_spec_init_err_missing_in_module(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(
        VoltConfigError, match="engine 'FooEngine' not found in module 'volt.engines'"
    ):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module="volt.engines:FooEngine",
            klass=None,
        )


def test_engine_spec_init_err_invalid_specifier_class(mocker: MockerFixture) -> None:

    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    with pytest.raises(VoltConfigError, match="invalid engine class specifier"):
        EngineSpec(
            id="mock",
            config=m_config,
            theme=m_theme,
            source="mock",
            opts={"bzzt": True},
            module=None,
            klass="is-not-identifier",
        )


def test_engine_spec_load_err_engines_file_missing(
    tmp_path: Path,
    isolated_project_dir: Callable,
) -> None:

    with isolated_project_dir(tmp_path, "ok_extended") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        theme = Theme.from_config(config)

        assert theme.engines_module_path.exists()
        theme.engines_module_path.unlink()

        with pytest.raises(VoltConfigError, match="theme engines file not found"):
            EngineSpec(
                id="gallery",
                config=config,
                theme=theme,
                source="gallery",
                opts={"foo": 1},
                module=None,
                klass="GalleryEngine",
            )


def test_engine_spec_load_err_engine_missing(
    tmp_path: Path,
    isolated_project_dir: Callable,
) -> None:

    with isolated_project_dir(tmp_path, "ok_extended") as project_dir:

        config = Config.from_file_name(
            invoc_dir=project_dir,
            project_dir=project_dir,
            config_file_name=constants.CONFIG_FILE_NAME,
        )
        theme = Theme.from_config(config)

        with pytest.raises(VoltConfigError, match="engine 'ImageEngine' not found"):
            EngineSpec(
                id="gallery",
                config=config,
                theme=theme,
                source="gallery",
                opts={"foo": 1},
                module=None,
                klass="ImageEngine",
            )


def test_engine_spec_load_err_static_engine(mocker: MockerFixture) -> None:
    m_config = mocker.MagicMock()
    m_theme = mocker.MagicMock()

    spec = EngineSpec(
        id="mock",
        config=m_config,
        theme=m_theme,
        source="foo",
        opts={"foo": 1},
        module="volt.engines:StaticEngine",
        klass=None,
    )

    with pytest.raises(
        VoltConfigError,
        match="if specified, 'source' must be 'static' for StaticEngine",
    ):
        spec.load()


@pytest.mark.parametrize(
    "target, ref, exp",
    [
        # target is the same as ref
        (Path("/a"), Path("/a"), Path(".")),
        (Path("/a/b"), Path("/a/b"), Path(".")),
        # target is a child of ref
        (Path("/a/b"), Path("/a"), Path("b")),
        (Path("/a/b/c"), Path("/a/b"), Path("c")),
        (Path("/a/b/c"), Path("/a"), Path("b/c")),
        # target is a sibling of ref
        (Path("/b"), Path("/a"), Path("../b")),
        (Path("/a/c"), Path("/a/b"), Path("../c")),
        # target and ref shares a common parent
        (Path("/a/b/c"), Path("/a/d/f"), Path("../../b/c/")),
        (Path("/a/b/c/d"), Path("/a/b/d/x/z/q"), Path("../../../../c/d")),
        (Path("/a/b/c/d/e/f"), Path("/a/x/y/z"), Path("../../../b/c/d/e/f")),
    ],
)
def test__calc_relpath_ok(target, ref, exp):
    obs = _calc_relpath(target, ref)
    assert obs == exp


@pytest.mark.parametrize(
    "target, ref",
    [
        (Path("a"), Path("a/b")),
        (Path("a/b"), Path("a")),
        (Path("/a"), Path("a/b")),
        (Path("a"), Path("/a/b")),
    ],
)
def test__calc_relpath_fail(target, ref):
    with pytest.raises(
        ValueError,
        match="could not compute relative paths of non-absolute input paths",
    ):
        _calc_relpath(target, ref)
