# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from os import path
from collections import Mapping

import toml

from .utils import lazyproperty, Result

__all__ = ["CONFIG_FNAME", "DEFAULT_CONFIG", "SiteConfig"]


# Config file name
CONFIG_FNAME = "volt.toml"

# Default configuration values
DEFAULT_CONFIG = {
    "volt": {
        "contents_path": "contents",
        "templates_path": "templates",
        "assets_path": path.join("templates", "assets"),
        "site_path": "site",
        "engines_path": "engines",
        "nested_content_lookup": True,
    },
    "site": {
        "dot_html_url": True,
    }
}

# Raw configuration text content for a new init
INIT_CONFIG_STR = """# Volt configuration file

# Site-level configuration
[site]
name = ""
url = ""
"""


class SiteConfig(dict):

    """Container for site-level configuration values."""

    defaults = DEFAULT_CONFIG

    @classmethod
    def from_toml(cls, work_path, toml_fname):
        """Creates configuration instance from the given TOML config file.

        The loaded TOML configuration will update the default config values.
        If the ``toml_path`` parameter is None, the default configuration
        will be returned without any change.

        :param str toml_fname: Name of the YAML config file.
        :param path work_path: Absolute path to the working directory.
        :returns: a :class:`volt.utils.Result` object that contains the result
            of a successful config loading, or a list of error messages, if
            any.

        """
        conf = cls(work_path, cls.defaults)
        if toml_fname is None:
            return Result.as_success(conf)

        with open(toml_fname) as src:
            try:
                user_conf = toml.load(src)
            except (IndexError, toml.TomlDecodeError):
                # TODO: display traceback depending on log level
                return Result.as_failure("config can not be parsed")

        # TODO: implement proper validation
        errors = cls.validate(user_conf)
        if errors:
            return Result.as_failure(errors)
        cls.nested_update(conf, user_conf)
        # TODO; resolve any engines and plugins config?
        return Result.as_success(conf)

    def __init__(self, work_path, defaults=None):
        super(SiteConfig, self).__init__(defaults or {})
        self.work_path = work_path.resolve()

    @classmethod
    def nested_update(cls, one, other):
        """Update function that respects nested values.

        This is similar to Python's dict.update, except when the value to
        be updated is an instance of :class:`collections.Mapping`, the
        function will recurse.

        """
        for key, value in other.items():
            if isinstance(value, Mapping):
                nv = cls.nested_update(one.get(key, {}), value)
                one[key] = nv
            else:
                one[key] = other[key]
        return one

    @classmethod
    def validate(cls, contents):
        """Performs validation of the config contents.

        :returns: Validation error messages as a list of strings.

        """
        errors = []
        if not isinstance(contents, dict) or not contents:
            # No point in progressing further if contents is not dictionary
            return ["unexpected config structure"]
        return errors

    @lazyproperty
    def contents_path(self):
        """Path to the Volt contents directory."""
        return self.work_path.joinpath(self["volt"]["contents_path"])

    @lazyproperty
    def templates_path(self):
        """Path to the Volt templates directory."""
        return self.work_path.joinpath(self["volt"]["templates_path"])

    @lazyproperty
    def site_path(self):
        """Path to the Volt site directory."""
        return self.work_path.joinpath(self["volt"]["site_path"])

    @lazyproperty
    def assets_path(self):
        """Path to the Volt assets directory."""
        return self.work_path.joinpath(self["volt"]["assets_path"])

    @lazyproperty
    def site(self):
        """Returns the site-level configuration."""
        return self.get("site", {})

    def for_engine(self, name):
        """Returns an engine-level configuration given its name."""
        return self.get("engines", {}).get(name, {})
