# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from types import MappingProxyType

import toml

from .utils import Result

__all__ = ["CONFIG_FNAME", "Config", "SessionConfig", "EngineConfig"]


# Default config file name.
CONFIG_FNAME = "volt.toml"


class Config(dict):

    """Base configuration object."""

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(f"config has no attribute {attr!r}")

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError as e:
            raise AttributeError(f"config has no attribute {attr!r}")


class SessionConfig(Config):

    """Container for session-level configuration values."""

    def __init__(self, pwd, site_conf=None, engines_conf=None,
                 contents_src="contents", templates_src="templates",
                 static_src="static", engines_src="engines", site_dest="site",
                 timezone=None, dot_html_url=True):
        """Initializes a site-level configuration.

        :param pathlib.Path pwd: Path to the project working directory.
        :param dict site_conf: Dictionary containing site configuration values.
        :param list engines_conf: List containing engine configuration values.
        :param str contents_src: Base directory name for content lookup.
        :param str templates_src: Base directory name for template lookup.
        :param str static_src: Base directory name for static files lookup.
        :param str site_src: Base directory name for site output.
        :param str timezone: Geographical timezone name for default timestamp
            interpretation.
        :param bool dot_html_url: Whether to output URLs with ``.html`` or not.

        """
        pwd = pwd.resolve()
        self.pwd = pwd

        site_conf = Config(site_conf or {})

        # Resolve path-related configs with current work path.
        pca_map = {
            "contents_src": contents_src,
            "templates_src": templates_src,
            "static_src": static_src,
            "engines_src": engines_src,
            "site_dest": site_dest,
        }
        for path_confv, argv in pca_map.items():
            finalv = pwd.joinpath(getattr(site_conf, path_confv, argv))
            setattr(site_conf, path_confv, finalv)

        # Resolve other configs.
        ca_map = {
            "dot_html_url": dot_html_url,
            "timezone": timezone,
        }
        for confv, argv in ca_map.items():
            finalv = getattr(site_conf, confv, argv)
            setattr(site_conf, confv, finalv)

        self.site = site_conf
        site_conf_proxy = MappingProxyType(site_conf)
        self.engines = [EngineConfig(site_conf_proxy, **ec)
                        for ec in (engines_conf or [])]

    @classmethod
    def from_toml(cls, pwd, toml_fname=CONFIG_FNAME):
        """Creates a site configuration from a Volt TOML file.

        :param pathlib.Path pwd: Path to the project working directory.
        :param str toml_fname: Name of TOML file containing the configuration
            values.
        :returns: a :class:``volt.utils.Result`` object that contains the
            result of a successful config loading, or a list of error messages,
            if any.

        """
        with open(toml_fname) as src:
            try:
                user_conf = toml.load(src)
            except (IndexError, toml.TomlDecodeError):
                # TODO: display traceback depending on log level
                return Result.as_failure("cannot parse config")

        # TODO: implement proper validation
        site_conf = user_conf.pop("site", {})
        if not isinstance(site_conf, dict):
            return Result.as_failure("unexpected config structure")
        engines_conf = user_conf.pop("engines", [])

        try:
            conf = cls(pwd, site_conf=site_conf, engines_conf=engines_conf)
        except Exception as e:
            return Result.as_failure(e.args[0])
        else:
            return Result.as_success(conf)


class EngineConfig(Config):

    """Container for engine-level configuration values."""

    def __init__(self, site_config, **kwargs):
        self.site_config = site_config

        # Required config values with predefined defaults.
        self.groups = kwargs.pop("groups", None) or []
        self.group_order = kwargs.pop("group_order", None) or {}
        self.group_size = kwargs.pop("group_size", 10)
        self.unit_permalink = kwargs.pop("unit_permalink", "{slug}")

        # Required config values with site-level defaults.
        ck = "dot_html_url"
        setattr(self, ck, kwargs.pop(ck, site_config[ck]))

        # Required config values with name-dependent defaults.
        name = kwargs.pop("name")
        self.name = name

        self.class_location = kwargs.pop("class_location", None) or \
            f"volt.engines.{name}"
        self.unit_class_location = kwargs.pop("unit_class_location", None) or \
            "volt.units:UnitSource"

        site_path = (kwargs.pop("site_path", None) or f"{name}").lstrip("/")
        self.site_path = site_path

        self.contents_src = site_config["contents_src"].joinpath(
            kwargs.pop("contents_src", None) or name)
        self.site_dest = site_config["site_dest"].joinpath(site_path)

        # Other user-defined engine values.
        for k, v in kwargs.items():
            setattr(self, k, v)
