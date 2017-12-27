# -*- coding: utf-8 -*-
"""
    volt.unit
    ~~~~~~~~~

    Unit parsing and creation.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import re
from pathlib import Path

import yaml
from iso8601 import parse_date
from slugify import slugify
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from yaml.scanner import ScannerError

from .utils import AttrDict, Result

__all__ = ["Unit"]


# Regex pattern for splitting front matter and the rest of unit.
_RE_WITH_FM = re.compile(r"\n---\n+")

# Regex pattern for splitting comma-separated tags
_RE_TAGS = re.compile(r",\s+")


class Unit(object):

    """A single source of text-related content."""

    __slots__ = ("src", "config", "metadata", "raw_text")

    @staticmethod
    def parse_metadata(raw: str, config: "SiteConfig",
                       src: Path) -> Result[AttrDict]:
        """Parses the unit metadata into a mapping.

        :param str raw: Raw metadata ready for parsing as YAML.
        :param volt.config.SiteConfig config: Site-wide configurations.
        :param pathlib.Path src: Path to the unit from which the metadata
            was parsed.
        :returns: The metadata as a mapping or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        try:
            meta = yaml.load(raw, Loader=Loader) or {}
        except ScannerError as e:
            return Result.as_failure(f"malformed metadata: {src}")

        # Ensure tags is a list of strings.
        tags = meta.get("tags", [])
        if not isinstance(tags, (tuple, list)):
            meta["tags"] = _RE_TAGS.split(str(tags))
        elif tags:
            meta["tags"] = tags

        # Transform pub_time to timezone-aware datetime object.
        if "pub_time" in meta:
            dto = parse_date(meta["pub_time"], default_timezone=None)
            if dto.tzinfo is not None:
                meta["pub_time"] = dto
            elif "timezone" in config:
                meta["pub_time"] = config.timezone.localize(dto)

        # Ensure title is supplied.
        if "title" not in meta:
            meta["title"] = src.stem

        if "slug" not in meta:
            # Set slug from title if not supplied.
            meta["slug"] = slugify(meta["title"])
        else:
            # .. or ensure that user supplied values are slugs.
            meta["slug"] = slugify(meta["slug"])

        return Result.as_success(AttrDict(meta))

    @classmethod
    def load(cls, src: Path, config: "SiteConfig",
             encoding="utf-8") -> "Result[Unit]":
        """Creates the unit by loading from the given path.

        :param pathlib.Path src: Path to the unit source.
        :param volt.config.SiteConfig config: Site-wide configurations.
        :param str encoding: Name of the unit source encoding.
        :returns: An instance of the unit or an error message indicating
            failure.
        :rtype: :class:`Result`

        """
        try:
            raw_bytes = src.read_bytes()
        except OSError as e:
            return Result.as_failure(e.strerror)

        try:
            raw_contents = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            return Result.as_failure(
                "decoding error: cannot decode"
                f" {str(src.relative_to(config.pwd))!r} using"
                f" {encoding!r}")

        split_contents = _RE_WITH_FM.split(raw_contents, 1)

        try:
            raw_meta, raw_text = split_contents
        except ValueError:
            return Result.as_failure(
                f"malformed unit: {str(src.relative_to(config.pwd))!r}")

        rmeta = cls.parse_metadata(raw_meta, config, src)
        if rmeta.is_failure:
            return rmeta

        return Result.as_success(cls(src, config, rmeta.data, raw_text))

    def __init__(self, src: Path, config: "SiteConfig", metadata: AttrDict,
                 raw_text: str) -> None:
        """Initializes the unit.

        :param pathlib.Path src: Path to the unit source.
        :param volt.config.SiteConfig config: Site-wide configurations.
        :param volt.utils.AttrDict metadata: Unit metadata.
        :param str raw_text: Raw text contents of the unit.

        """
        self.src = src
        self.config = config
        self.metadata = metadata
        self.raw_text = raw_text
