# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

from collections import UserDict
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Optional, cast

import yaml
from pendulum.tz.timezone import Timezone
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from . import exceptions as exc
from .utils import calc_relpath, get_tz

__all__ = ["CONFIG_FNAME", "SiteConfig"]


# Default config file name.
CONFIG_FNAME = "volt.yaml"

# Type aliases.
RawConfig = Dict[str, Any]


class SiteConfig(UserDict):

    """Container for site-level configuration values."""

    @classmethod
    def from_raw_config(
        cls,
        cwd: Path,
        pwd: Path,
        user_conf: RawConfig,
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

        return cls(cwd=cwd, pwd=pwd, user_conf=user_conf)

    @classmethod
    def from_yaml(
        cls,
        cwd: Path,
        pwd: Path,
        yaml_fname: str = CONFIG_FNAME,
    ) -> "SiteConfig":
        """Create a site configuration from a Volt YAML file.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project working directory.
        :param yaml_fname: Name of YAML file containing the configuration
            values.

        :returns: A site config instance.

        :raises ~exc.VoltConfigError: when validation fails.

        """
        with (pwd / yaml_fname).open() as src:
            try:
                user_conf = cast(Dict[str, Any], yaml.safe_load(src))
            except (ParserError, ScannerError) as e:
                # TODO: display traceback depending on log level
                raise exc.VoltConfigError(
                    f"could not parse config: {e.args[0]}"
                ) from e

        return cls.from_raw_config(cwd=cwd, pwd=pwd, user_conf=user_conf)

    def __init__(
        self,
        cwd: Path,
        pwd: Path,
        src_dirname: str = "src",
        out_dirname: str = "dist",
        contents_dirname: str = "contents",
        scaffold_dirname: str = "scaffold",
        theme_dirname: str = "theme",
        timezone: Optional[Timezone] = None,
        user_conf: Optional[dict] = None,
    ) -> None:
        """Initialize a site-level configuration.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project directory.
        :param src_dirname: Base directory name for site source.
        :param out_dirname: Base directory name for site output.
        :param timezone: Timezone for default timestamp interpretation.

        """
        super().__init__(user_conf)
        self._pwd = pwd
        self._cwd = cwd
        self._src_path = pwd / src_dirname
        self._out_path = pwd / out_dirname
        self._src_contents_path = self._src_path / contents_dirname
        self._src_scaffold_path = self._src_path / scaffold_dirname
        self._src_theme_path = self._src_path / theme_dirname

    @cached_property
    def pwd(self) -> Path:
        """Path to the project directory."""
        self._pwd

    @cached_property
    def cwd(self) -> Path:
        """Path to the invocation directory."""
        self._cwd

    @cached_property
    def src_path(self) -> Path:
        """Path to the site source directory."""
        return self._src_path

    @cached_property
    def out_path(self) -> Path:
        """Path to the site output directory."""
        return self._out_path

    @cached_property
    def out_relpath(self) -> Path:
        """Path to the site output directory relative to the invocation
        directory."""
        return calc_relpath(self._out_path, self.cwd)

    @cached_property
    def src_contents_path(self) -> Path:
        """Path to the site source contents."""
        return self._src_contents_path

    @cached_property
    def src_scaffold_path(self) -> Path:
        """Path to the site source scaffold."""
        return self._src_scaffold_path

    @cached_property
    def src_theme_path(self) -> Path:
        """Path to the site source theme."""
        return self._src_theme_path
