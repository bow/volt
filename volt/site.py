# -*- coding: utf-8 -*-
"""
    volt.site
    ~~~~~~~~~

    Site-level functions and classes.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import jinja2.exceptions as j2exc

from .utils import Result


class Site(object):

    """Representation of the static site."""

    def __init__(self, session_config, template_env):
        self.session_config = session_config
        self.template_env = template_env

    def gather_units(self, pattern="*.md"):
        site_config = self.session_config.site
        unit_cls = site_config.unit_cls

        units = []
        for unit_path in site_config.contents_src.glob(pattern):
            res = unit_cls.load(unit_path, site_config)
            if res.is_failure:
                return res
            units.append(res.data)

        return Result.as_success(units)

    def build(self):
        runits = self.gather_units()
        if runits.is_failure:
            return runits

        session_config = self.session_config

        ut_fname = session_config.site.unit_template_fname
        try:
            template = self.template_env.get_template(ut_fname)
        except j2exc.TemplateNotFound:
            return Result.as_failure(f"cannot find template {ut_fname!r}")
        except j2exc.TemplateSyntaxError as e:
            return Result.as_failure(f"template {ut_fname!r} has syntax"
                                     f" errors: {e.message}")

        site_dest = session_config.site.site_dest
        for unit in runits.data:
            target = site_dest.joinpath(f"{unit.metadata.slug}.html")
            try:
                template.stream(unit=unit).dump(str(target))
            except j2exc.UndefinedError as e:
                return Result.as_failure(
                    "cannot write"
                    f" {str(target.relative_to(session_config.pwd))!r} using"
                    f" {ut_fname!r}: {e.message}")

        return Result.as_success(None)
