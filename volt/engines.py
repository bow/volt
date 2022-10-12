"""Site engines."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
from typing import Any, Sequence

from .config import SiteConfig
from .targets import Target


class Engine(abc.ABC):

    """Object for creating site targets."""

    def __init__(self, config: SiteConfig, *args: Any, **kwargs: Any) -> None:
        self.config = config
        self.options = kwargs.pop("options", {})

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        raise NotImplementedError()
