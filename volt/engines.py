# -*- coding: utf-8 -*-
"""
    volt.engines
    ~~~~~~~~~~~~

    Engine-related classses and functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import abc
import os
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment

from .targets import PageTarget, Target
from .units import Unit
from .utils import load_template, Result

__all__ = ["BlogEngine", "Engine"]


class Engine(abc.ABC):

    """Builder for a site section."""

    def __init__(self, config: "SectionConfig",
                 template_env: Environment) -> None:
        self.config = config
        self.template_env = template_env

    @property
    def unit_class(self) -> Unit:
        """The unit class of this engine."""
        return Unit

    @staticmethod
    def default_config() -> Dict[str, Any]:
        """Default engine configuration values

        Subclasses should override this static method with the default engine
        configuration values.

        """
        return {}

    def gather_units(self, ext: str=".md",
                     drafts_dirname: str="drafts") -> Result[List[Unit]]:
        """Gathers all of the engine units except ones in the drafts
        directory."""
        config = self.config
        unit = self.unit_class
        units = []

        dirs = [config["contents_src"]]
        while dirs:
            cur = dirs.pop()
            for de in os.scandir(cur):
                if de.name.endswith(ext) and de.is_file():
                    runit = unit.load(Path(de.path), config)
                    if runit.is_failure:
                        return runit
                    units.append(runit.data)
                elif de.name != drafts_dirname and de.is_dir():
                    dirs.append(de.path)

        return Result.as_success(units)

    def create_unit_pages(self, units: List[Unit]) -> Result[List[PageTarget]]:
        """Creates :class:`PageTarget` instances of units.

        :parameter list units: List of units to turn into pages.
        :returns: A list of created pages or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        rtemplate = load_template(self.template_env,
                                  self.config["unit_template"])
        if rtemplate.is_failure:
            return rtemplate

        pages = []
        dest_rel = self.config["site_dest_rel"]
        for unit in units:
            dest = dest_rel.joinpath(f"{unit.metadata['slug']}.html")
            rrend = PageTarget.from_template(unit, dest, rtemplate.data)
            if rrend.is_failure:
                return rrend
            pages.append(rrend.data)

        return Result.as_success(pages)

    @abc.abstractmethod
    def create_targets(self) -> Result[List[Target]]:
        """Creates all the targets of the section.

        Subclasses must override this method.

        """


class BlogEngine(Engine):

    """Engine for creating blog sections."""

    def create_targets(self) -> Result[List[Target]]:
        runits = self.gather_units()
        if runits.is_failure:
            return runits

        return self.create_unit_pages(runits.data)
