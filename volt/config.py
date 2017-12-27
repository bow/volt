# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib.parse import urljoin as urljoin

import toml
from pytz.tzinfo import DstTzInfo

from .units import Unit
from .utils import import_mod_attr, get_tz, AttrDict, Result

__all__ = ["CONFIG_FNAME", "SiteConfig", "SectionConfig"]


# Default config file name.
CONFIG_FNAME = "Volt.toml"

# Type aliases.
RawConfig = Dict[str, Any]


def validate_site_conf(value: RawConfig) -> Result[RawConfig]:
    """Validates the given site config value.

    :param dict value: Site config mapping to validate.
    :returns: The input value upon successful validation or an error message
        when validation fails.
    :rtype: :class:`Result`.

    """
    if not isinstance(value, dict):
        return Result.as_failure("site config must be a mapping")

    # Keys whose values must be nonempty strings.
    for strk in ("timezone", "unit", "unit_template"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            return Result.as_failure(f"site config {strk!r} must be a"
                                     " nonempty string")

    # Keys whose values must be strings representing relative paths.
    for pathk in ("contents_src", "templates_src", "assets_src", "site_dest"):
        if pathk not in value:
            continue
        uv = value[pathk]
        if isinstance(uv, str) or not uv:
            return Result.as_failure(f"site config {pathk!r} must be a"
                                     " nonempty string")
        if os.path.isabs(uv):
            return Result.as_failure(f"site config {pathk!r} must be a"
                                     " relative path")

    # Keys whose value must be booleans.
    for bk in ("dot_html_url", "hide_first_pagination_idx"):
        if bk not in value:
            continue
        if not isinstance(value[bk], bool):
            return Result.as_failure(f"site config {bk!r} must be a boolean")

    # Section config must be a dictionary.
    if "section" in value and not isinstance(value["section"], dict):
        return Result.as_failure("section config must be a mapping")

    return Result.as_success(value)


def validate_section_conf(name: str, value: RawConfig) -> Result[RawConfig]:
    """Validates a single section config.

    :param str name: Name of the section config to validate.
    :param dict value: Section config mapping to validate.
    :returns: The input value upon successful validation or an error message
        when validation fails.
    :rtype: :class:`Result`.

    """
    if not isinstance(value, dict):
        return Result.as_failure(f"section config {name!r} must be a mapping")

    infix = f"of section {name!r}"

    # Keys whose value must be booleans.
    for bk in ("dot_html_url", "hide_first_pagination_idx"):
        if bk not in value:
            continue
        if not isinstance(value[bk], bool):
            return Result.as_failure(f"config {bk!r} {infix} must be a"
                                     " boolean")

    # Keys whose values must be positive nonzero integers.
    intk = "pagination_size"
    if intk in value:
        uv = value[intk]
        if not isinstance(uv, int) or uv < 1:
            return Result.as_failure(f"config {intk!r} {infix} must be a"
                                     " positive, nonzero integer")

    # Keys whose values must be nonempty strings.
    for strk in ("path", "engine", "unit", "unit_template",
                 "unit_path_pattern", "pagination_template"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            return Result.as_failure(f"config {strk!r} {infix} must be a"
                                     " nonempty string")

    # Keys whose values must be strings representing relative paths.
    pathk = "contents_src"
    if pathk in value:
        uv = value[pathk]
        if isinstance(uv, str) or not uv:
            return Result.as_failure(f"config {pathk!r} {infix} must be a"
                                     " nonempty string")
        if os.path.isabs(uv):
            return Result.as_failure(f"config {pathk!r} {infix} must be a"
                                     " relative path")

    # Keys whose value must be dictionaries of specific structures.
    vfm = {
        "paginations": validate_section_pagination,
        "unit_order": validate_section_unit_order,
    }
    for dk, vf in vfm.items():
        vr = vf(name, value, dk)
        if vr.is_failure:
            return vr

    return Result.as_success((name, value))


def validate_section_pagination(name: str, section_config: RawConfig,
                                key: str) -> Result[RawConfig]:
    """Validates the pagination value of the given section config value.

    :param str name: Name of the section config in which the pagination config
        exists.
    :param dict section_config: Section config to validate.
    :param str key: Name of the key whose value is the pagination config.
    :returns: The input section config upon successful validation or an error
        message when validation fails.
    :rtype: :class:`Result`.

    """
    infix = f"of section {name!r}"

    if key in section_config:
        value = section_config[key]
        if not isinstance(value, dict):
            return Result.as_failure(f"config {key!r} {infix} must be a"
                                     " mapping")
        # Assumes keys are strings.
        for k, v in value.items():
            # path_pattern: str
            ikey1 = "path_pattern"
            if ikey1 not in v:
                print(k, v)
                return Result.as_failure(
                    f"config '{key}.{k}.{ikey1}' {infix} must be present")
            v1 = v[ikey1]
            if not isinstance(v1, str) or not v1:
                return Result.as_failure(
                    f"config '{key}.{k}.{ikey1}' {infix} must be a nonempty"
                    " string")
            if "{idx}" not in v1:
                return Result.as_failure(
                    f"config '{key}.{k}.{ikey1}' {infix} must contain the"
                    " '{idx}' template")

            # size: int
            ikey2 = "size"
            if ikey2 in v:
                v2 = v[ikey2]
                if not isinstance(v2, int) or v2 < 1:
                    return Result.as_failure(
                        f"config '{key}.{k}.{ikey2}' {infix} must be a"
                        " positive, nonzero integer")

            # pagination_template: str
            ikey3 = "pagination_template"
            if ikey3 in v:
                v3 = v[ikey3]
                if not isinstance(v3, str) or not v3:
                    return Result.as_failure(
                        f"config '{key}.{k}.{ikey3}' {infix} must be a"
                        " nonempty string")

    return Result.as_success(section_config)


def validate_section_unit_order(name: str, section_config: RawConfig,
                                key: str) -> Result[RawConfig]:
    """Validates the unit_order value of the given section config value.

    :param str name: Name of the section config in which the unit_order config
        exists.
    :param dict section_config: Section config to validate.
    :param str key: Name of the key whose value is the unit_order config.
    :returns: The input section config upon successful validation or an error
        message when validation fails.
    :rtype: :class:`Result`.

    """
    infix = f"of section {name!r}"

    if key in section_config:
        value = section_config[key]
        if not isinstance(value, dict):
            return Result.as_failure(f"config {key!r} {infix} must be a"
                                     " mapping")
        if "key" not in value:
            return Result.as_failure("config '{key}.key' {infix} must be"
                                     " present")
        iv = value["key"]
        if not isinstance(iv, str) or not iv:
            return Result.as_failure("config '{key}.key' {infix} must be a"
                                     " nonempty string")
        if "reverse" in value and not isinstance(value["reverse"], bool):
            return Result.as_failure("config '{key}.reverse' {infix} must be a"
                                     " boolean")

    return Result.as_success(section_config)


class SiteConfig(AttrDict):

    """Container for site-level configuration values."""

    def __init__(self, pwd: Path,
                 user_site_conf: Optional[RawConfig]=None,
                 user_sections_conf: Optional[RawConfig]=None,
                 contents_src: str="contents",
                 templates_src: str="templates",
                 assets_src: str="assets",
                 site_dest: str="site",
                 timezone: Optional[DstTzInfo]=None,
                 dot_html_url: bool=True,
                 unit: Unit=Unit,
                 unit_template: str="page.html",
                 hide_first_pagination_idx: bool=True) -> None:
        """Initializes a site-level configuration.

        If a non-None ``user_site_conf`` and/or ``user_sections_conf`` are
        given, this method will consume their contents.

        :param pathlib.Path pwd: Path to the project working directory.
        :param user_site_conf: Dictionary containing user-supplied site
            configuration values.
        :type user_site_conf: dict or None
        :param user_sections_conf: Dictionary containing user-supplied section
            configuration values, keyed by the section name.
        :type user_sections_conf: dict or None
        :param str contents_src: Base directory name for content lookup.
        :param str templates_src: Base directory name for template lookup.
        :param str assets_src: Base directory name for assets lookup.
        :param str site_src: Base directory name for site output.
        :param timezone: Timezone for default timestamp interpretation.
        :type timezone: pytz.tzinfo.DstTzInfo or None
        :param bool dot_html_url: Whether to output URLs with ``.html`` or not.
        :param volt.site.Unit unit: Unit class used for creating the
            site's units.
        :param str unit_template: File name of the template used for
            the site's units. This file must exist in the expected template
            directory.
        :param bool hide_first_pagination_idx: Whether to show the first
            pagination's ``idx`` in its URL or not.

        """
        pwd = pwd.resolve()
        user_site_conf = AttrDict(user_site_conf or {})

        # Resolve path-related configs with current work path.
        # TODO: Move this to .from_toml?
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
        for confv, argv in ca_map.items():
            self[confv] = user_site_conf.pop(confv, argv)

        # Move other custom configs.
        for k in list(user_site_conf.keys()):
            self[k] = user_site_conf.pop(k)

        self.pwd = pwd
        self.sections = {name: SectionConfig(name, self, **sc)
                         for name, sc in (user_sections_conf or {}).items()}

    @classmethod
    def from_user_conf(cls, pwd: Path,
                       user_conf: RawConfig,
                       site_vfunc: Callable[[RawConfig], Result[RawConfig]]=
                       validate_site_conf,
                       section_vfunc: Callable[[RawConfig], Result[RawConfig]]=
                       validate_section_conf) -> "Result[SiteConfig]":
        """Creates a ``SiteConfig`` from the given user-supplied config.

        :param pathlib.Path pwd: Path to project directory.
        :param dict user_conf: Raw user config.
        :param callable site_vfunc: Callable for validating the ``site``
            configuration. The callable must accept a single site config value
            as input and return a :class:`Result`.
        :param callable section_vfunc: Callable for validating each section
            config in the site config. The callable must a accept a single
            section config value as input and return a :class:`Result`.
        :returns: The site config or an error message if it cannot be created.
        :rtype: :class:`Result`

        """
        vres = site_vfunc(user_conf.pop("site", {}))
        if vres.is_failure:
            return vres
        site_conf = vres.data

        # Get timezone from config or system.
        rtz = get_tz(site_conf.get("timezone", None))
        if rtz.is_failure:
            return rtz
        site_conf["timezone"] = rtz.data

        # Import user-defined unit if specified.
        if "unit" in site_conf:
            rucls = import_mod_attr(site_conf["unit"])
            if rucls.is_failure:
                return rucls
            site_conf["unit"] = rucls.data

        sections_conf = user_conf.pop("section", {})
        for name, sc in sections_conf.items():
            svres = section_vfunc(name, sc)
            if svres.is_failure:
                return svres

        conf = cls(pwd, user_site_conf=site_conf,
                   user_sections_conf=sections_conf)

        return Result.as_success(conf)

    @classmethod
    def from_toml(cls, pwd, toml_fname=CONFIG_FNAME) -> "Result[SiteConfig]":
        """Creates a site configuration from a Volt TOML file.

        :param pathlib.Path pwd: Path to the project working directory.
        :param str toml_fname: Name of TOML file containing the configuration
            values.
        :returns: A dictionary or an error message if it cannot be created.
        :rtype: :class:`Result`

        """
        with pwd.joinpath(toml_fname).open() as src:
            try:
                user_conf = toml.load(src)
            except (IndexError, toml.TomlDecodeError) as e:
                # TODO: display traceback depending on log level
                return Result.as_failure(f"cannot parse config: {e.args[0]}")

        return cls.from_user_conf(pwd, user_conf)


class SectionConfig(AttrDict):

    """Container for section-specific configuration values."""

    def __init__(self, name: str, site_config: SiteConfig, **kwargs) -> None:
        """Initializes a section-level configuration.

        :param str name: Name of the section.
        :param volt.config.SiteConfig site_config: The site config in which
            the section config exists.

        """
        self.name = name
        self.site_config = site_config

        # Required config values with predefined defaults.
        paginations = kwargs.pop("paginations", None) or {}
        pagination_size = kwargs.pop("pagination_size", 10)
        for pv in paginations.values():
            pv.setdefault("pagination_size", pagination_size)

        self.paginations = paginations
        self.pagination_size = pagination_size
        self.unit_order = kwargs.pop("unit_order", None) or \
            {"key": "pub_time", "reverse": True}

        # Required config values with site-level defaults.
        for ck in ("dot_html_url", "hide_first_pagination_idx"):
            setattr(self, ck, kwargs.pop(ck, site_config[ck]))

        # Required config values with name-dependent defaults.
        try:
            spath = kwargs.pop("path")
            spath = "/" + spath if not spath.startswith("/") else spath
        except KeyError:
            spath = f"/{name}"
        self.path = spath

        try:
            upath = urljoin(f"{spath}/", kwargs.pop("unit_path_pattern"))
        except KeyError:
            upath = f"{spath}/{{slug}}"
        self.unit_path_pattern = upath

        self.engine = kwargs.pop("engine", None) or \
            f"volt.engines.{name.capitalize()}Engine"
        self.unit = kwargs.pop("unit", None) or "volt.units.Unit"

        self.site_dest = site_config["site_dest"].joinpath(spath[1:])
        self.contents_src = site_config["contents_src"].joinpath(
            kwargs.pop("contents_src", None) or name)

        # Other user-defined engine values.
        for k, v in kwargs.items():
            setattr(self, k, v)
