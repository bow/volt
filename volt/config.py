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
from typing import Any, Callable, Dict, Optional
from urllib.parse import urljoin as urljoin

import toml
from pytz.tzinfo import DstTzInfo

from .units import Unit
from .utils import import_mod_attr, get_tz, Result

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

    # Keys whose values must be strings.
    for strk in ("name", "url"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str):
            return Result.as_failure(f"site config {strk!r} must be a string")

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
        if not isinstance(uv, str) or not uv:
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
        if (not isinstance(uv, int) or isinstance(uv, bool)) or uv < 1:
            return Result.as_failure(f"config {intk!r} {infix} must be a"
                                     " positive, nonzero integer")

    # Keys whose values must be nonempty strings.
    for strk in ("path", "engine", "unit", "unit_template",
                 "pagination_template"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            return Result.as_failure(f"config {strk!r} {infix} must be a"
                                     " nonempty string")

    # Keys whose values must be strings representing relative paths.
    for pathk in ("contents_src", "unit_path_pattern"):
        if pathk not in value:
            continue
        uv = value[pathk]
        if not isinstance(uv, str) or not uv:
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
                    " '{idx}' wildcard")

            # size: int
            ikey2 = "size"
            if ikey2 in v:
                v2 = v[ikey2]
                if (not isinstance(v2, int) or isinstance(v2, bool)) or v2 < 1:
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

    return Result.as_success((name, section_config, key))


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
            return Result.as_failure(f"config '{key}.key' {infix} must be"
                                     " present")
        iv = value["key"]
        if not isinstance(iv, str) or not iv:
            return Result.as_failure(f"config '{key}.key' {infix} must be a"
                                     " nonempty string")
        if "reverse" in value and not isinstance(value["reverse"], bool):
            return Result.as_failure(f"config '{key}.reverse' {infix} must be"
                                     " a boolean")

    return Result.as_success((name, section_config, key))


class SiteConfig(dict):

    """Container for site-level configuration values."""

    def __init__(self, cwd: Path, pwd: Path,
                 user_site_conf: Optional[RawConfig]=None,
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

        :param pathlib.Path cwd: Path to the invocation directory.
        :param pathlib.Path pwd: Path to the project directory.
        :param user_site_conf: Dictionary containing user-supplied site
            configuration values.
        :type user_site_conf: dict or None
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
        for confv, argv in ca_map.items():
            self[confv] = user_site_conf.pop(confv, argv)

        # Move other custom configs.
        self.update(**user_site_conf)

        # Config values that cannot be overwritten.
        self["pwd"] = pwd
        self["cwd"] = cwd
        self["sections"] = {}

    def add_section(self, name: str, section_conf: RawConfig) -> Result[None]:
        """Adds the given section config to the site config after loading the
        relevant engine.

        :param str name: Section name of the config.
        :param dict conf: Section config to add.
        :returns: None or an error message indicating failure.
        :rtype: :class:`Result`

        """
        rsc = SectionConfig.from_raw_configs(name, section_conf, self)
        if rsc.is_failure:
            return rsc
        self["sections"][name] = rsc.data
        return Result.as_success(None)

    @classmethod
    def from_raw_config(
            cls, cwd: Path, pwd: Path, user_conf: RawConfig,
            site_vfunc: Callable[[RawConfig], Result[RawConfig]]=
            validate_site_conf,
            section_vfunc: Callable[[RawConfig], Result[RawConfig]]=
            validate_section_conf) -> "Result[SiteConfig]":
        """Creates a ``SiteConfig`` from the given user-supplied config.

        :param pathlib.Path cwd: Path to invocation directory.
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
        if "site" not in user_conf:
            return Result.as_failure("cannot find site configuration in config"
                                     " file")
        vres = site_vfunc(user_conf.pop("site"))
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

        conf = cls(cwd, pwd, user_site_conf=site_conf)

        sections_conf = user_conf.pop("section", {})
        for name, sc in sections_conf.items():
            svres = section_vfunc(name, sc)
            if svres.is_failure:
                return svres
            ares = conf.add_section(name, sc)
            if ares.is_failure:
                return ares

        return Result.as_success(conf)

    @classmethod
    def from_toml(cls, cwd: Path, pwd: Path,
                  toml_fname: str=CONFIG_FNAME) -> "Result[SiteConfig]":
        """Creates a site configuration from a Volt TOML file.

        :param pathlib.Path cwd: Path to the invocation directory.
        :param pathlib.Path pwd: Path to the project working directory.
        :param str toml_fname: Name of TOML file containing the configuration
            values.
        :returns: A site config instance or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        with pwd.joinpath(toml_fname).open() as src:
            try:
                user_conf = toml.load(src)
            except (IndexError, toml.TomlDecodeError) as e:
                # TODO: display traceback depending on log level
                return Result.as_failure(f"cannot parse config: {e.args[0]}")

        return cls.from_raw_config(cwd, pwd, user_conf)


class SectionConfig(ChainMap):

    """Container for section-specific configuration values."""

    def __init__(self, name: str, user_conf: RawConfig, eng_conf: RawConfig,
                 site_conf: SiteConfig) -> None:
        """Initializes a section-level configuration.

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

        :param str name: Name of the section.
        :param dict user_conf: Validated user config.
        :param dict eng_conf: Validated engine-defined config defaults.
        :param volt.config.SiteConfig site_config: The site config in which
            the section config exists.

        """
        super().__init__(user_conf, eng_conf, site_conf)
        self["name"] = name

    @classmethod
    def from_raw_configs(cls, name: str, user_conf: RawConfig,
                         site_conf: SiteConfig) -> "Result[SectionConfig]":
        """Creates a section config from the given raw configurations.

        This method may mutate some or all of its input configs.

        :param str name: Name of the section.
        :param dict user_conf: Raw user config.
         :param volt.config.SiteConfig site_config: The site config in which
             the section config exists.
        :param site_defaults: Keys whose value defaults to the site config.
        :type site_defaults: iterable of string
        :returns: A section config or an error message indicating failure.
        :rtype: :class:`Result`

        """
        vures = validate_section_conf(name, user_conf)
        if vures.is_failure:
            return vures

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

        def resolve(key):
            return user_conf.pop(key, default_conf[key])

        eng_name = resolve("engine")
        reng = import_mod_attr(eng_name)
        if reng.is_failure:
            return reng
        eng = reng.data

        try:
            eng_conf = eng.default_config()
        except (AttributeError, TypeError):
            # AttributeError: when eng is not an Engine subclass.
            # TypeError: when eng defines default_config as an instance method.
            return Result.as_failure(
                f"cannot load default config of {eng_name}")
        veres = validate_section_conf(name, eng_conf)
        if veres.is_failure:
            return veres

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

        conf = cls(name, resolved, eng_conf, site_conf)

        return Result.as_success(conf)
