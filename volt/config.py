# -*- coding: utf-8 -*-
"""
    volt.config
    ~~~~~~~~~~~

    Configuration handling.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import toml

from .units import Unit
from .utils import import_mod_attr, get_tz, AttrDict, Result

__all__ = ["CONFIG_FNAME", "SessionConfig", "SectionConfig"]


# Default config file name.
CONFIG_FNAME = "volt.toml"


class SessionConfig(AttrDict):

    """Container for session-level configuration values."""

    def __init__(self, pwd, site_conf=None, sections_conf=None,
                 contents_src="contents", templates_src="templates",
                 static_src="static", engines_src="engines", site_dest="site",
                 timezone=None, dot_html_url=True, unit_cls=Unit,
                 unit_template_fname="site_unit.html"):
        """Initializes a site-level configuration.

        :param pathlib.Path pwd: Path to the project working directory.
        :param dict site_conf: Dictionary containing site configuration values.
        :param dict sections_conf: Dictionary containing section configuration
            values, keyed by the section name.
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

        """
        pwd = pwd.resolve()
        self.pwd = pwd

        site_conf = AttrDict(site_conf or {})

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
            "unit_cls": unit_cls,
            "unit_template_fname": unit_template_fname,
        }
        for confv, argv in ca_map.items():
            finalv = getattr(site_conf, confv, argv)
            setattr(site_conf, confv, finalv)

        site_conf.pwd = pwd
        self.site = site_conf
        self.sections = {name: SectionConfig(site_conf, name, **sc)
                         for name, sc in (sections_conf or {}).items()}

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

        try:
            conf = cls(pwd, site_conf=site_conf, sections_conf=sections_conf)
        except Exception as e:
            return Result.as_failure(e.args[0])
        else:
            return Result.as_success(conf)


class SectionConfig(AttrDict):

    """Container for section-specific configuration values."""

    def __init__(self, site_config, name, **kwargs):
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
        self.name = name

        self.engine = kwargs.pop("engine", None) or \
            f"volt.engines.{name.capitalize()}Engine"
        self.unit = kwargs.pop("unit", None) or "volt.units.Unit"

        site_path = (kwargs.pop("site_path", None) or f"{name}").lstrip("/")
        self.site_path = site_path

        self.contents_src = site_config["contents_src"].joinpath(
            kwargs.pop("contents_src", None) or name)
        self.site_dest = site_config["site_dest"].joinpath(site_path)

        # Other user-defined engine values.
        for k, v in kwargs.items():
            setattr(self, k, v)
