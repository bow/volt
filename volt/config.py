"""Configuration handling."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

import os
from collections import UserDict
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Optional, cast

import yaml
from jinja2 import Environment, FileSystemLoader, Template
from pendulum.tz.timezone import Timezone
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from . import constants
from . import exceptions as excs
from .utils import find_dir_containing, get_tz, load_template

__all__ = ["SiteConfig"]

# Type aliases.
RawConfig = Dict[str, Any]


class SiteConfig(UserDict):

    """Container for site-level configuration values."""

    @classmethod
    def from_project_yaml(
        cls,
        cwd: Path,
        start_lookup_dir: Optional[Path] = None,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> Optional["SiteConfig"]:
        """Create an instance from within a project directory.

        This methods performs an upwards traversal from within the current
        directory to look for a YAML config file and loads it.

        :param cwd: Path to invocation directory.
        :param start_lookup_dir: Path to the directory from which project
            directory lookup should start. If set to ``None``, the lookup will
            start from the current directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        """
        start_lookup_dir = start_lookup_dir or cwd
        pwd = find_dir_containing(yaml_fname, start_lookup_dir)
        if pwd is None:
            return None

        return cls.from_yaml(
            cwd=cwd,
            pwd=pwd.resolve(),
            yaml_fname=yaml_fname,
            **kwargs,
        )

    @classmethod
    def from_raw_config(
        cls,
        cwd: Path,
        pwd: Path,
        user_conf: RawConfig,
        **kwargs: Any,
    ) -> "SiteConfig":
        """Create an instance from the given user-supplied config.

        :param cwd: Path to invocation directory.
        :param pwd: Path to project directory.
        :param user_conf: Raw user config.

        :returns: The site config.

        :raises ~volt.exceptions.VoltTimezoneError: when the config timezone
            name is invalid.
        :raises ~volt.exceptions.VoltConfigError: when any other
            configuration-related error occurs.

        """
        # Get timezone from config or system.
        tz = get_tz(user_conf.get("timezone", None))
        user_conf["timezone"] = tz

        return cls(cwd=cwd, pwd=pwd, user_conf=user_conf, **kwargs)

    @classmethod
    def from_yaml(
        cls,
        cwd: Path,
        pwd: Path,
        yaml_fname: str = constants.CONFIG_FNAME,
        **kwargs: Any,
    ) -> "SiteConfig":
        """Create a site configuration from a Volt YAML file.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project working directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        :returns: A site config instance.

        :raises ~exc.VoltConfigError: when validation fails.

        """
        yaml_fp = pwd / yaml_fname
        with yaml_fp.open() as src:
            try:
                user_conf = cast(Dict[str, Any], yaml.safe_load(src))
            except (ParserError, ScannerError) as e:
                # TODO: display traceback depending on log level
                raise excs.VoltConfigError(
                    f"could not parse config: {e.args[0]}"
                ) from e

        return cls.from_raw_config(
            cwd=cwd,
            pwd=pwd,
            user_conf=user_conf,
            yaml_fp=yaml_fp,
            **kwargs,
        )

    def __init__(
        self,
        cwd: Path,
        pwd: Path,
        src_dirname: str = constants.SITE_SRC_DIRNAME,
        out_dirname: str = constants.SITE_OUT_DIRNAME,
        contents_dirname: str = constants.SITE_CONTENTS_DIRNAME,
        static_dirname: str = constants.SITE_STATIC_DIRNAME,
        theme_dirname: str = constants.SITE_THEME_DIRNAME,
        template_dirname: str = constants.SITE_THEME_TEMPLATES_DIRNAME,
        drafts_dirname: str = constants.SITE_DRAFTS_DIRNAME,
        ext_dirname: str = constants.SITE_EXT_DIRNAME,
        xcmd_script_fname: str = constants.SITE_XCMD_SCRIPT_FNAME,
        timezone: Optional[Timezone] = None,
        yaml_fp: Optional[Path] = None,
        user_conf: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a site-level configuration.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project directory.
        :param src_dirname: Base directory name for site source.
        :param out_dirname: Base directory name for site output.
        :param timezone: Timezone for default timestamp interpretation.

        """
        super().__init__(user_conf, **kwargs)
        self._pwd = pwd
        self._cwd = cwd
        self._src_path = pwd / src_dirname
        self._out_path = pwd / out_dirname
        self._src_contents_path = self._src_path / contents_dirname
        self._src_ext_path = self._src_path / ext_dirname
        self._src_drafts_path = self._src_path / drafts_dirname
        self._src_static_path = self._src_path / static_dirname
        self._theme_path = self._src_path / theme_dirname
        self._theme_template_path = self._theme_path / template_dirname
        self._xcmd_script_path = self._src_ext_path / xcmd_script_fname
        self._yaml_fp = yaml_fp

    @cached_property
    def pwd(self) -> Path:
        """Path to the project root directory."""
        return self._pwd

    @cached_property
    def cwd(self) -> Path:
        """Path to the invocation directory."""
        return self._cwd

    @cached_property
    def rel_pwd(self) -> Path:
        """Path to the project directory, relative from invocation directory."""
        rel = self.cwd.relative_to(self.pwd)
        return Path("/".join(("..",) * len(rel.parts)))

    @cached_property
    def src_path(self) -> Path:
        """Path to the site source directory."""
        return self._src_path

    @cached_property
    def out_path(self) -> Path:
        """Path to the site output directory."""
        return self._out_path

    @cached_property
    def src_contents_path(self) -> Path:
        """Path to the site contents."""
        return self._src_contents_path

    @cached_property
    def src_drafts_path(self) -> Path:
        """Path to the site draft contents."""
        return self._src_drafts_path

    @cached_property
    def src_static_path(self) -> Path:
        """Path to the site source static files."""
        return self._src_static_path

    @cached_property
    def theme_path(self) -> Path:
        """Path to the site source theme."""
        return self._theme_path

    @cached_property
    def theme_static_path(self) -> Path:
        """Path to the site source theme static files."""
        return self.theme_path / "static"

    @cached_property
    def theme_template_path(self) -> Path:
        """Path to the theme template directory."""
        return self._theme_template_path

    @cached_property
    def num_common_parts(self) -> int:
        return len(self.src_path.parts) + 1

    @cached_property
    def template_env(self) -> Environment:
        """Theme template environment."""
        return Environment(  # nosec
            loader=FileSystemLoader(self.theme_template_path),
            auto_reload=True,
            enable_async=True,
        )

    @cached_property
    def theme_config(self) -> Dict[str, Any]:
        fp = self.theme_path / constants.THEME_SETTINGS_FNAME
        with fp.open("r") as src:
            return cast(Dict[str, Any], yaml.safe_load(src))

    @cached_property
    def xcmd_script_path(self) -> Optional[Path]:
        """Path to a custom CLI extension, if present."""
        fp = self._xcmd_script_path
        if fp.exists():
            return fp
        return None

    @cached_property
    def in_docker(self) -> bool:
        return os.path.exists("/.dockerenv")

    def load_template(self, name: str) -> Template:
        """Load a template with the given name."""
        return load_template(self.template_env, name)

    def load_theme_template(
        self,
        key: str = constants.DEFAULT_TEMPLATE_KEY,
    ) -> Template:
        """Load a theme template with the given key."""

        theme_templates = self.theme_config["templates"]

        try:
            template_name = theme_templates[key]
        except KeyError as e:
            raise excs.VoltResourceError(
                f"could not find template {key!r} in theme settings"
            ) from e

        template = self.load_template(template_name)

        return template

    def reload(self) -> "SiteConfig":
        """Reloads a YAML config."""
        if self._yaml_fp is None:
            raise excs.VoltResourceError("could not reload non-YAML config")
        return self.__class__.from_yaml(cwd=self.cwd, pwd=self.pwd)
