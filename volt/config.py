# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from os import path
from types import MappingProxyType

import toml

from .utils import Result

__all__ = ["CONFIG_FNAME", "Config", "SessionConfig"]


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

    def __init__(self, pwd, site_conf=None,
                 contents_src="contents", templates_src="templates",
                 assets_src=path.join("templates", "assets"),
                 engines_src="engines", site_dest="site",
                 recursive_contents_lookup=True, dot_html_url=True):
        """Initializes a site-level configuration.

        :param pathlib.Path pwd: Path to the project working directory.
        :param dict site_conf: Dictionary containing site configuration values.
        :param str contents_dname: Base directory name for content lookup.
        :param str templates_dname: Base directory name for template lookup.
        :param str assets_dname: Base directory name for assets lookup.
        :param str site_dname: Base directory name for site output.
        :param bool dot_html_url: Whether to output URLs with ``.html`` or not.
        :param bool recursive_contents_lookup: Whether to search for contents
            recursively or not.

        """
        pwd = pwd.resolve()
        self.pwd = pwd

        site_conf = Config(site_conf or {})

        # Resolve path-related configs with current work path.
        pca_map = {
            "contents_src": contents_src,
            "templates_src": templates_src,
            "assets_src": assets_src,
            "engines_src": engines_src,
            "site_dest": site_dest,
        }
        for path_confv, argv in pca_map.items():
            finalv = pwd.joinpath(getattr(site_conf, path_confv, argv))
            setattr(site_conf, path_confv, finalv)

        # Resolve other configs.
        ca_map = {
            "recursive_contents_lookup": recursive_contents_lookup,
            "dot_html_url": dot_html_url,
        }
        for confv, argv in ca_map.items():
            finalv = getattr(site_conf, confv, argv)
            setattr(site_conf, confv, finalv)

        self.site = site_conf

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
                return Result.as_failure("config can not be parsed")

        # TODO: implement proper validation
        site_conf = user_conf.pop("site", {})
        if not isinstance(site_conf, dict):
            return Result.as_failure("unexpected config structure")

        try:
            conf = cls(pwd, site_conf=site_conf)
        except Exception as e:
            return Result.as_failure(e.args[0])
        else:
            return Result.as_success(conf)
