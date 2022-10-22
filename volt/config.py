"""Configuration handling."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import os
from collections import UserDict
from contextvars import ContextVar
from functools import cached_property
from pathlib import Path
from typing import cast, Any, Dict, Iterable, Optional

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from . import constants
from . import error as err


_use_color_key = "use-color"
_use_color: ContextVar[bool] = ContextVar(_use_color_key, default=True)


def get_use_color() -> bool:
    return cast(bool, _use_color.get(_use_color_key))


def set_use_color(value: bool) -> bool:
    token = _use_color.set(value)
    return cast(bool, token.old_value)


class Config(UserDict):

    """Container for site-level configuration values."""

    @classmethod
    def from_project_dir(
        cls,
        invoc_dir: Path,
        start_lookup_dir: Path,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> Optional["Config"]:
        """Create an instance from within a project directory.

        This methods performs an upwards traversal from within the current
        directory to look for a YAML config file and loads it.

        :param invoc_dir: Path to invocation directory.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        """
        project_dir = _find_dir_containing(yaml_fname, start_lookup_dir)
        if project_dir is None:
            return None

        return cls.from_yaml(
            invoc_dir=invoc_dir,
            project_dir=project_dir.resolve(),
            yaml_fname=yaml_fname,
            **kwargs,
        )

    @classmethod
    def from_yaml(
        cls,
        invoc_dir: Path,
        project_dir: Path,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> "Config":
        """Create a site configuration from a Volt YAML file.

        :param invoc_dir: Path to the invocation directory.
        :param project_dir: Path to the project working directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        :returns: A site config instance.

        :raises ~exc.VoltConfigError: when validation fails.

        """
        yaml_file = project_dir / yaml_fname
        with yaml_file.open() as src:
            try:
                user_conf = cast(Dict[str, Any], yaml.safe_load(src))
            except (ParserError, ScannerError) as e:
                # TODO: display traceback depending on log level
                raise err.VoltConfigError(f"could not parse config: {e.args[0]}") from e

        return cls(
            invoc_dir=invoc_dir,
            project_dir=project_dir,
            user_conf=user_conf,
            yaml_file=yaml_file,
            **kwargs,
        )

    def __init__(
        self,
        invoc_dir: Path,
        project_dir: Path,
        project_dirname: str = constants.SITE_PROJECT_DIRNAME,
        target_dirname: str = constants.SITE_TARGET_DIRNAME,
        sources_dirname: str = constants.SITE_SOURCES_DIRNAME,
        themes_dirname: str = constants.SITE_THEMES_DIRNAME,
        static_dirname: str = constants.SITE_STATIC_DIRNAME,
        drafts_dirname: str = constants.SITE_DRAFTS_DIRNAME,
        extension_dirname: str = constants.SITE_EXTENSION_DIRNAME,
        xcmd_script_fname: str = constants.SITE_XCMD_SCRIPT_FNAME,
        yaml_file: Optional[Path] = None,
        user_conf: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a site-level configuration.

        :param invoc_dir: Path to the invocation directory.
        :param project_dir: Path to the project directory.
        :param src_dirname: Base directory name for site source.
        :param out_dirname: Base directory name for site output.

        """
        uc = user_conf or {}
        self._with_drafts: bool = uc.pop("with_drafts", False)
        self._name: str = uc.pop("name", "")
        self._url: str = uc.pop("url", "")
        self._slug_replacements: Iterable[Iterable[str]] = (
            uc.pop("slug_replacements", None) or constants.DEFAULT_SLUG_REPLACEMENTS
        )
        self._theme_config: Optional[dict] = uc.pop("theme", None) or None
        super().__init__(user_conf, **kwargs)

        self._invoc_dir = invoc_dir
        self._project_dir = project_dir / project_dirname
        self._target_dir = project_dir / target_dirname
        self._sources_dir = self._project_dir / sources_dirname
        self._themes_dir = self._project_dir / themes_dirname
        self._extension_dir = self._project_dir / extension_dirname
        self._drafts_dirname = drafts_dirname
        self._static_dir = self._project_dir / static_dirname
        self._xcmd_script = self._extension_dir / xcmd_script_fname
        self._yaml_file = yaml_file

    @cached_property
    def name(self) -> str:
        """Name of the site."""
        return self._name

    @cached_property
    def url(self) -> str:
        """URL of the site."""
        return self._url

    @cached_property
    def theme(self) -> Optional[dict]:
        """Theme configurations."""
        return self._theme_config

    @cached_property
    def slug_replacements(self) -> Iterable[Iterable[str]]:
        """Slug replacements rules."""
        return self._slug_replacements

    @cached_property
    def project_dir(self) -> Path:
        """Path to the project root directory."""
        return self._project_dir

    @cached_property
    def project_dir_rel(self) -> Path:
        """Path to the project directory, relative from invocation directory."""
        rel = self.invoc_dir.relative_to(self.project_dir)
        return Path("/".join(("..",) * len(rel.parts)))

    @cached_property
    def invoc_dir(self) -> Path:
        """Path to the invocation directory."""
        return self._invoc_dir

    @cached_property
    def target_dir(self) -> Path:
        """Path to the site output directory."""
        return self._target_dir

    @cached_property
    def sources_dir(self) -> Path:
        """Path to the site source contents."""
        return self._sources_dir

    @cached_property
    def themes_dir(self) -> Path:
        """Path to the site themes directory."""
        return self._themes_dir

    @cached_property
    def drafts_dirname(self) -> str:
        """Name of the drafts directory."""
        return self._drafts_dirname

    @cached_property
    def static_dir(self) -> Path:
        """Path to the site source static files."""
        return self._static_dir

    @cached_property
    def num_common_parts(self) -> int:
        return len(self.project_dir.parts) + 1

    @cached_property
    def xcmd_script(self) -> Optional[Path]:
        """Path to a custom CLI extension, if present."""
        fp = self._xcmd_script
        if fp.exists():
            return fp
        return None

    @cached_property
    def with_drafts(self) -> bool:
        """Whether to publish draft contents or not."""
        return self._with_drafts

    @cached_property
    def in_docker(self) -> bool:
        return os.path.exists("/.dockerenv")

    def reload(self) -> "Config":
        """Reloads a YAML config."""
        if self._yaml_file is None:
            raise err.VoltResourceError("could not reload non-YAML config")
        return self.__class__.from_yaml(
            invoc_dir=self.invoc_dir, project_dir=self.project_dir
        )


def _find_dir_containing(fname: str, start: Path) -> Optional[Path]:
    """Find the directory containing the filename.

    Directory lookup is performed from the given start directory up until the
    root (`/`) directory. If no start directory is given, the lookup starts
    from the current directory.

    :param fname: The filename that should be present in the directory.
    :param start: The path from which lookup starts.

    :returns: The path to the directory that contains the filename or None if
        no such path can be found.

    """
    cur = Path(start).expanduser().resolve()

    while cur != cur.parent:
        if cur.joinpath(fname).exists():
            return cur
        cur = cur.parent

    return None
