"""Site engines."""
# (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>

import abc
from pathlib import Path
from typing import Any, Sequence

from .config import SiteConfig
from .targets import Target


class Engine(abc.ABC):

    """Object for creating site targets."""

    def __init__(
        self,
        config: SiteConfig,
        source_dirname: str = "",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.source_dirname = source_dirname
        self.config = config
        self.options = kwargs.pop("options", {})

    @property
    def source_dir(self) -> Path:
        """Path to the root source directory for this engine."""
        return self.config.sources_path / self.source_dirname

    @property
    def source_drafts_dir(self) -> Path:
        """Path to the source drafts directory for this engine."""
        return self.source_dir / self.config.drafts_dirname

    @abc.abstractmethod
    def create_targets(self) -> Sequence[Target]:
        raise NotImplementedError()
