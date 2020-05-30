# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os
from collections import ChainMap
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, cast
from urllib.parse import urljoin as urljoin

import yaml
from pytz.tzinfo import DstTzInfo
from yaml.parser import ParserError

from . import exceptions as exc
from .units import Unit
from .utils import calc_relpath, get_tz, import_mod_attr

__all__ = ["CONFIG_FNAME", "SiteConfig", "SectionConfig"]


# Default config file name.
CONFIG_FNAME = "volt.yaml"

# Type aliases.
RawConfig = Dict[str, Any]


def validate_site_conf(value: RawConfig) -> None:
    """Validate the given site config value.

    :param value: Site config mapping to validate.

    :raises ~exc.VoltConfigError: when validation fails.

    """
    if not isinstance(value, dict):
        raise exc.VoltConfigError("site config must be a mapping")

    # Keys whose values must be strings.
    for strk in ("name", "url"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str):
            raise exc.VoltConfigError(f"site config {strk!r} must be a string")

    # Keys whose values must be nonempty strings.
    for strk in ("timezone", "unit", "unit_template"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            raise exc.VoltConfigError(
                f"site config {strk!r} must be a nonempty string"
            )

    # Keys whose values must be strings representing relative paths.
    for pathk in ("contents_src", "templates_src", "assets_src", "site_dest"):
        if pathk not in value:
            continue
        uv = value[pathk]
        if not isinstance(uv, str) or not uv:
            raise exc.VoltConfigError(
                f"site config {pathk!r} must be a nonempty string"
            )
        if os.path.isabs(uv):
            raise exc.VoltConfigError(
                f"site config {pathk!r} must be a relative path"
            )

    # Keys whose value must be booleans.
    for bk in ("dot_html_url", "hide_first_pagination_idx"):
        if bk not in value:
            continue
        if not isinstance(value[bk], bool):
            raise exc.VoltConfigError(f"site config {bk!r} must be a boolean")

    # Section config must be a dictionary.
    if "section" in value and not isinstance(value["section"], dict):
        raise exc.VoltConfigError("section config must be a mapping")

    return None


def validate_section_conf(name: str, value: RawConfig) -> None:
    """Validate a single section config.

    :param name: Name of the section config to validate.
    :param value: Section config mapping to validate.

    :raises ~exc.VoltConfigError: when validation fails.

    """
    if not isinstance(value, dict):
        raise exc.VoltConfigError(f"section config {name!r} must be a mapping")

    infix = f"of section {name!r}"

    # Keys whose value must be booleans.
    for bk in ("dot_html_url", "hide_first_pagination_idx"):
        if bk not in value:
            continue
        if not isinstance(value[bk], bool):
            raise exc.VoltConfigError(
                f"config {bk!r} {infix} must be a boolean"
            )

    # Keys whose values must be positive nonzero integers.
    intk = "pagination_size"
    if intk in value:
        uv = value[intk]
        if (not isinstance(uv, int) or isinstance(uv, bool)) or uv < 1:
            raise exc.VoltConfigError(
                f"config {intk!r} {infix} must be a positive, nonzero integer"
            )

    # Keys whose values must be nonempty strings.
    for strk in (
        "path", "engine", "unit", "unit_template", "pagination_template",
    ):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            raise exc.VoltConfigError(
                f"config {strk!r} {infix} must be a nonempty string"
            )

    # Keys whose values must be strings representing relative paths.
    for pathk in ("contents_src", "unit_path_pattern"):
        if pathk not in value:
            continue
        uv = value[pathk]
        if not isinstance(uv, str) or not uv:
            raise exc.VoltConfigError(
                f"config {pathk!r} {infix} must be a nonempty string"
            )
        if os.path.isabs(uv):
            raise exc.VoltConfigError(
                f"config {pathk!r} {infix} must be a relative path"
            )

    # Keys whose value must be dictionaries of specific structures.
    vfm = {
        "paginations": validate_section_pagination,
        "unit_order": validate_section_unit_order,
    }
    for dk, vf in vfm.items():
        vf(name, value, dk)

    return None


def validate_section_pagination(
    name: str,
    section_config: RawConfig,
    key: str,
) -> None:
    """Validate the pagination value of the given section config value.

    :param name: Name of the section config in which the pagination config
        exists.
    :param section_config: Section config to validate.
    :param key: Name of the key whose value is the pagination config.

    :raises ~exc.VoltConfigError: when validation fails.

    """
    if key not in section_config:
        return None

    infix = f"of section {name!r}"

    value = section_config[key]
    if not isinstance(value, dict):
        raise exc.VoltConfigError(f"config {key!r} {infix} must be a mapping")

    # Assumes keys are strings.
    for k, v in value.items():
        # path_pattern: str
        ikey1 = "path_pattern"
        if ikey1 not in v:
            raise exc.VoltConfigError(
                f"config '{key}.{k}.{ikey1}' {infix} must be present"
            )
        v1 = v[ikey1]
        if not isinstance(v1, str) or not v1:
            raise exc.VoltConfigError(
                f"config '{key}.{k}.{ikey1}' {infix} must be a nonempty string"
            )
        if "{idx}" not in v1:
            raise exc.VoltConfigError(
                f"config '{key}.{k}.{ikey1}' {infix} must contain the '{{idx}}'"
                " wildcard"
            )

        # size: int
        ikey2 = "size"
        if ikey2 in v:
            v2 = v[ikey2]
            if (not isinstance(v2, int) or isinstance(v2, bool)) or v2 < 1:
                raise exc.VoltConfigError(
                    f"config '{key}.{k}.{ikey2}' {infix} must be a positive,"
                    " nonzero integer"
                )

        # pagination_template: str
        ikey3 = "pagination_template"
        if ikey3 in v:
            v3 = v[ikey3]
            if not isinstance(v3, str) or not v3:
                raise exc.VoltConfigError(
                    f"config '{key}.{k}.{ikey3}' {infix} must be a nonempty"
                    " string"
                )

    return None


def validate_section_unit_order(
    name: str,
    section_config: RawConfig,
    key: str,
) -> None:
    """Validates the unit_order value of the given section config value.

    :param str name: Name of the section config in which the unit_order config
        exists.
    :param dict section_config: Section config to validate.
    :param str key: Name of the key whose value is the unit_order config.

    :raises ~exc.VoltConfigError: when validation fails.

    """
    infix = f"of section {name!r}"

    if key in section_config:
        value = section_config[key]
        if not isinstance(value, dict):
            raise exc.VoltConfigError(
                f"config {key!r} {infix} must be a mapping"
            )
        if "key" not in value:
            raise exc.VoltConfigError(
                f"config '{key}.key' {infix} must be present"
            )
        iv = value["key"]
        if not isinstance(iv, str) or not iv:
            raise exc.VoltConfigError(
                f"config '{key}.key' {infix} must be a nonempty string"
            )
        if "reverse" in value and not isinstance(value["reverse"], bool):
            raise exc.VoltConfigError(
                f"config '{key}.reverse' {infix} must be a boolean"
            )

    return None


class SiteConfig(dict):

    """Container for site-level configuration values."""

    def __init__(
        self,
        cwd: Path,
        pwd: Path,
        user_site_conf: Optional[RawConfig] = None,
        contents_src: str = "contents",
        templates_src: str = "templates",
        assets_src: str = "assets",
        site_dest: str = "site",
        timezone: Optional[DstTzInfo] = None,
        dot_html_url: bool = True,
        unit: Type[Unit] = Unit,
        unit_template: str = "page.html",
        hide_first_pagination_idx: bool = True,
    ) -> None:
        """Initialize a site-level configuration.

        If a non-None ``user_site_conf`` and/or ``user_sections_conf`` are
        given, this method will consume their contents.

        :param cwd: Path to the invocation directory.
        :param pwd: Path to the project directory.
        :param Dictionary containing user-supplied site configuration values.
        :param contents_src: Base directory name for content lookup.
        :param templates_src: Base directory name for template lookup.
        :param assets_src: Base directory name for assets lookup.
        :param site_src: Base directory name for site output.
        :param Timezone for default timestamp interpretation.
        :param dot_html_url: Whether to output URLs with the .html extension or
            not.
        :param unit: Unit class used for creating the site's units.
        :param unit_template: File name of the template used for the site's
            units. This file must exist in the expected template directory.
        :param hide_first_pagination_idx: Whether to show the first
            pagination's ``idx`` in its URL or not.

        """
        pwd = pwd.resolve()
        cwd = cwd.resolve()
        user_site_conf = user_site_conf or {}

        # Resolve path-related configs with current work path.
        pca_map = {
            "contents_src": contents_src,
            "templates_src": templates_src,
            "assets_src": assets_src,
            "site_dest": site_dest,
        }
        for path_confv, argv in pca_map.items():
            try:
                finalv = user_site_conf.pop(path_confv)
            except KeyError:
                finalv = argv
            self[path_confv] = pwd.joinpath(finalv)

        # Resolve other configs with defaults set in kwargs.
        ca_map = {
            "dot_html_url": dot_html_url,
            "hide_first_pagination_idx": hide_first_pagination_idx,
            "timezone": timezone,
            "unit": unit,
            "unit_template": unit_template,
        }
        for confv, argv in ca_map.items():  # type: ignore
            self[confv] = user_site_conf.pop(confv, argv)

        # Move other custom configs.
        self.update(**user_site_conf)

        # Config values that could not be overwritten.
        self["pwd"] = pwd
        self["cwd"] = cwd
        self["sections"] = {}
        self["site_dest_rel"] = calc_relpath(self["site_dest"], cwd)

    def add_section(self, name: str, section_conf: RawConfig) -> None:
        """Add the given section config to the site config after loading the
        relevant engine.

        :param name: Section name of the config.
        :param conf: Section config to add.

        :returns: None or an error message indicating failure.

        """
        sc = SectionConfig.from_raw_configs(name, section_conf, self)
        self["sections"][name] = sc

        return None

    @classmethod
    def from_raw_config(
        cls,
        cwd: Path,
        pwd: Path,
        user_conf: RawConfig,
        site_vfunc: Callable[[RawConfig], Any] = validate_site_conf,
        section_vfunc: Callable[[str, RawConfig], Any] = validate_section_conf,
    ) -> "SiteConfig":
        """Create an instance from the given user-supplied config.

        :param cwd: Path to invocation directory.
        :param pwd: Path to project directory.
        :param user_conf: Raw user config.
        :param site_vfunc: Callable for validating the ``site`` configuration.
        :param section_vfunc: Callable for validating each section config in the
            site config.

        :returns: The site config.

        :raises ~volt.exceptions.VoltTimezoneError: when the config timezone
            name is invalid.
        :raises ~volt.exceptions.VoltConfigError: when any other
            configuration-related error occurs.

        """
        if "site" not in user_conf:
            raise exc.VoltConfigError(
                "could not find site configuration in config file"
            )

        site_conf = user_conf.pop("site")

        site_vfunc(site_conf)

        # Get timezone from config or system.
        tz = get_tz(site_conf.get("timezone", None))
        site_conf["timezone"] = tz

        # Import user-defined unit if specified.
        if "unit" in site_conf:
            site_conf["unit"] = import_mod_attr(site_conf["unit"])

        conf = cls(cwd, pwd, user_site_conf=site_conf)

        sections_conf = user_conf.pop("section", {})
        for name, sc in sections_conf.items():
            section_vfunc(name, sc)
            conf.add_section(name, sc)

        return conf

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
        with pwd.joinpath(yaml_fname).open() as src:
            try:
                user_conf = cast(Dict[str, Any], yaml.safe_load(src))
            except ParserError as e:
                # TODO: display traceback depending on log level
                raise exc.VoltConfigError(
                    f"could not parse config: {e.args[0]}"
                ) from e

        return cls.from_raw_config(cwd, pwd, user_conf)


class SectionConfig(ChainMap):

    """Container for section-specific configuration values."""

    def __init__(
        self,
        name: str,
        user_conf: RawConfig,
        eng_conf: RawConfig,
        site_conf: SiteConfig,
    ) -> None:
        """Initialize a section-level configuration.

        This method should rarely (if ever) be called by third parties.
        Instead, use :classmethod:`SectionConfig.from_raw_configs` to
        create instances of section configs.

        In general, section configuration have the following resolution order
        (sorted by precedence, from highest to lowest):

            * User-supplied values, given as ``user_section_conf``.
            * Engine-default values, given as the ``.default_config()`` static
              method of the given ``Engine``.
            * Site config values.

        It is assumed that any overriding values have the same type as the
        values they override. Validations should be done prior to calling this
        method.

        :param name: Name of the section.
        :param user_conf: Validated user config.
        :param eng_conf: Validated engine-defined config defaults.
        :param site_config: The site config in which the section config exists.

        """
        super().__init__(user_conf, eng_conf, site_conf)
        self["name"] = name

    @classmethod
    def from_raw_configs(
        cls,
        name: str,
        user_conf: RawConfig,
        site_conf: SiteConfig,
    ) -> "SectionConfig":
        """Create a section config from the given raw configurations.

        This method may mutate some or all of its input configs.

        :param name: Name of the section.
        :param user_conf: Raw user config.
        :param site_config: The site config in which the section config exists.

        :returns: A section config.

        :raises ~exc.VoltConfigError: when any validation error occurs.

        """
        validate_section_conf(name, user_conf)

        default_conf = {
            "paginations": {},
            "pagination_size": 10,
            "unit_order": {"key": "pub_time", "reverse": True},
            "unit": "volt.units.Unit",
            "path": f"/{name}",
            "contents_src": f"{name}",
            "engine": "volt.engines.BlogEngine",
            # Keys whose default values depend on other keys' values.
            "unit_path_pattern": None,
        }

        resolved = {}

        def resolve(key: str) -> Any:
            return user_conf.pop(key, default_conf[key])

        eng_name = resolve("engine")
        eng = import_mod_attr(eng_name)

        try:
            eng_conf = eng.default_config()
        except (AttributeError, TypeError) as e:
            # AttributeError: when eng is not an Engine subclass.
            # TypeError: when eng defines default_config as an instance method.
            raise exc.VoltConfigError(
                f"could not load default config of {eng_name}"
            ) from e

        validate_section_conf(name, eng_conf)

        # Required config values with predefined defaults.
        paginations = resolve("paginations")
        pagination_size = resolve("pagination_size")
        for pv in paginations.values():
            pv.setdefault("size", pagination_size)
        resolved["paginations"] = paginations
        resolved["pagination_size"] = pagination_size
        resolved["unit_order"] = resolve("unit_order")

        # Required config values with name-dependent defaults.
        path = resolve("path")
        path = f"/{path}" if not path.startswith("/") else path
        resolved["path"] = path

        upp = resolve("unit_path_pattern")
        upp = f"{path}/{{slug}}" if upp is None else urljoin(f"{path}/", upp)
        resolved["unit_path_pattern"] = upp

        resolved["contents_src"] = site_conf["contents_src"].joinpath(
            resolve("contents_src"))

        # Other user-defined values.
        resolved.update(**user_conf)

        # # Values that cannot be overwritten.
        resolved["engine"] = eng
        resolved["site_dest"] = site_conf["site_dest"].joinpath(path[1:])
        resolved["site_dest_rel"] = calc_relpath(
            resolved["site_dest"],
            site_conf["cwd"],
        )

        conf = cls(name, resolved, eng_conf, site_conf)

        return conf
