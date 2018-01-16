# -*- coding: utf-8 -*-
"""
    volt.engines
    ~~~~~~~~~~~~

    Engine-related classses and functions.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
from typing import Any, Dict

from jinja2 import Environment

__all__ = ["BlogEngine", "Engine"]


class Engine(object):

    """Builder for a site section."""

    def __init__(self, config: "SectionConfig",
                 template_env: Environment, plan: "SitePlan") -> None:
        self.config = config
        self.template_env = template_env
        self.plan = plan

    @staticmethod
    def default_config() -> Dict[str, Any]:
        """Default engine configuration values

        Subclasses should override this static method with the default engine
        configuration values.

        """
        return {}


class BlogEngine(Engine):

    """Engine for building blog sections."""
