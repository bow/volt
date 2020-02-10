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
from typing import Any, Dict, List, Sequence, Type

from jinja2 import Environment

from .config import SectionConfig
from .targets import PageTarget, Target
from .units import Unit
from .utils import load_template

__all__ = ["BlogEngine", "Engine"]


class Engine(abc.ABC):

    """Builder for a site section."""

    def __init__(
        self,
        config: SectionConfig,
        template_env: Environment,
    ) -> None:
        self.config = config
        self.template_env = template_env

    @property
    def unit_class(self) -> Type[Unit]:
        """The unit class of this engine."""
        return Unit

    @staticmethod
    def default_config() -> Dict[str, Any]:
        """Default engine configuration values

        Subclasses should override this static method with the default engine
        configuration values.

        """
        return {}

    def gather_units(
        self,
        ext: str = ".md",
        drafts_dirname: str = "drafts",
    ) -> List[Unit]:
        """Gather all engine units except ones in the drafts directory."""
        config = self.config
        unit_cls = self.unit_class
        units = []

        dirs = [config["contents_src"]]
        while dirs:
            cur = dirs.pop()
            for de in os.scandir(cur):
                if de.name.endswith(ext) and de.is_file():
                    unit = unit_cls.load(Path(de.path), config)
                    units.append(unit)
                elif de.name != drafts_dirname and de.is_dir():
                    dirs.append(de.path)

        return units

    def create_unit_pages(self, units: List[Unit]) -> List[PageTarget]:
        """Create :class:`PageTarget` instances of the given units.

        :param units: List of units to process.

        :returns: Pages of the given units.

        :raises ~volt.exceptions.VoltResourceError: when the unit template can
            not be loaded

        """
        template = load_template(
            self.template_env,
            self.config["unit_template"],
        )

        pages = []
        dest_rel = self.config["site_dest_rel"]
        pages = [
            PageTarget.from_template(
                unit,
                dest_rel / f"{unit.metadata['slug']}.html",
                template
            )
            for unit in units
        ]

        return pages

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        """Create all the targets of the section.

        Subclasses must override this method.

        """


class BlogEngine(Engine):

    """Engine for creating blog sections."""

    def create_targets(self) -> Sequence[Target]:
        units = self.gather_units()
        targets = self.create_unit_pages(units)

        return targets
