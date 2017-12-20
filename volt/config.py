# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from urllib.parse import urljoin as urljoin

import toml

from .units import Unit
from .utils import import_mod_attr, get_tz, AttrDict, Result

__all__ = ["CONFIG_FNAME", "SiteConfig", "SectionConfig"]


# Default config file name.
CONFIG_FNAME = "volt.toml"


class SiteConfig(AttrDict):

    """Container for site-level configuration values."""

    def __init__(self, pwd, user_site_conf=None, user_sections_conf=None,
                 contents_src="contents", templates_src="templates",
                 static_src="static", engines_src="engines", site_dest="site",
                 timezone=None, dot_html_url=True, unit_cls=Unit,
                 unit_template_fname="page.html",
                 hide_first_pagination_idx=True):
        """Initializes a site-level configuration.

        If a non-default ``user_site_conf`` is given, this method will consume
        its contents.

        :param pathlib.Path pwd: Path to the project working directory.
        :param dict user_site_conf: Dictionary containing user-supplied site
            configuration values.
        :param dict user_sections_conf: Dictionary containing user-supplied
            section configuration values, keyed by the section name.
        :param str contents_src: Base directory name for content lookup.
        :param str templates_src: Base directory name for template lookup.
        :param str static_src: Base directory name for static files lookup.
        :param str site_src: Base directory name for site output.
        :param str timezone: Geographical timezone name for default timestamp
            interpretation.
        :param bool dot_html_url: Whether to output URLs with ``.html`` or not.
        :param volt.site.Unit unit_cls: Unit class used for creating the
            site's units.
        :param str unit_template_fname: File name of the template used for
            the site's units. This file must exist in the expected template
            directory.
        :param bool hide_first_pagination_idx: Whether to show the first
            pagination's ``idx`` in its URL or not.

        """
        pwd = pwd.resolve()
        user_site_conf = AttrDict(user_site_conf or {})

        # Resolve path-related configs with current work path.
        pca_map = {
            "contents_src": contents_src,
            "templates_src": templates_src,
            "static_src": static_src,
            "engines_src": engines_src,
            "site_dest": site_dest,
        }
        for path_confv, argv in pca_map.items():
            self[path_confv] = pwd.joinpath(
                user_site_conf.pop(path_confv, argv))

        # Resolve other configs with defaults set in kwargs.
        ca_map = {
            "dot_html_url": dot_html_url,
            "hide_first_pagination_idx": hide_first_pagination_idx,
            "timezone": timezone,
            "unit_cls": unit_cls,
            "unit_template_fname": unit_template_fname,
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
    def from_toml(cls, pwd, toml_fname=CONFIG_FNAME):
        """Creates a site configuration from a Volt TOML file.

        :param pathlib.Path pwd: Path to the project working directory.
        :param str toml_fname: Name of TOML file containing the configuration
            values.
        :returns: a :class:``volt.utils.Result`` object that contains the
            result of a successful config loading, or a list of error messages,
            if any.

        """
        with pwd.joinpath(toml_fname).open() as src:
            try:
                user_conf = toml.load(src)
            except (IndexError, toml.TomlDecodeError):
                # TODO: display traceback depending on log level
                return Result.as_failure("cannot parse config")

        # TODO: implement proper validation
        site_conf = user_conf.pop("site", {})
        if not isinstance(site_conf, dict):
            return Result.as_failure("unexpected config structure")

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
            site_conf["unit_cls"] = rucls.data

        sections_conf = user_conf.pop("section", {})

        conf = cls(pwd, user_site_conf=site_conf,
                   user_sections_conf=sections_conf)

        return Result.as_success(conf)


class SectionConfig(AttrDict):

    """Container for section-specific configuration values."""

    def __init__(self, name, site_config, **kwargs):
        self.site_config = site_config

        # Required config values with predefined defaults.
        self.paginations = kwargs.pop("paginations", None) or []
        self.pagination_size = kwargs.pop("pagination_size", 10)
        self.unit_order = kwargs.pop("unit_order", None) or \
            {"key": "pub_time", "reverse": True}

        # Required config values with site-level defaults.
        for ck in ("dot_html_url", "hide_first_pagination_idx"):
            setattr(self, ck, kwargs.pop(ck, site_config[ck]))

        # Required config values with name-dependent defaults.
        self.name = name

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
