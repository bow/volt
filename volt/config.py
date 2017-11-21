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

    def __init__(self, work_path, defaults=None):
        """Initializes a site-level configuration.

        :param path work_path: Absolute path to the working directory.
        :param dict defaults: Default values for initialization.

        """
        super().__init__(defaults or self.defaults)
        self.work_path = work_path.resolve()

    def nested_update(self, one, other):
        """Update function that respects nested values.

        This is similar to Python's dict.update, except when the value to
        be updated is an instance of :class:`collections.Mapping`, the
        function will recurse.

        """
        for key, value in other.items():
            if isinstance(value, Mapping):
                nv = self.nested_update(one.get(key, {}), value)
                one[key] = nv
            else:
                one[key] = other[key]

        return one

    def update_with_toml(self, toml_fname):
        """Updates the configuration instance with the given TOML config file.

        :param str toml_fname: Name of the TOML config file.
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
        errors = self.validate(user_conf)
        if errors:
            return Result.as_failure(errors)
        self.nested_update(self, user_conf)

        # Move 'site' to root level.
        self.update(**self.pop("site"))
        # TODO; resolve any engines and plugins config?
        return Result.as_success(self)

    def validate(self, contents):
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
