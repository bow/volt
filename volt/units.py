# -*- coding: utf-8 -*-
"""
    volt.unit
    ~~~~~~~~~

    Unit parsing and creation.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Union

import yaml
from slugify import slugify
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from .utils import Result

if TYPE_CHECKING:
    from .config import SectionConfig, SiteConfig  # noqa: F401


__all__ = ["Unit"]


# Regex pattern for splitting front matter and the rest of unit.
_RE_WITH_FM = re.compile(r"\n---\n+")

# Regex pattern for splitting comma-separated tags
_RE_TAGS = re.compile(r",\s+")


def validate_metadata(value: Any) -> Result[dict]:
    """Validate the given metadata.

    :param dict value: Metadata to validate.

    :returns: The input value upon successful validation or an error message
        when validation fails.

    """
    if not isinstance(value, dict):
        return Result.as_failure("unit metadata must be a mapping")

    # Keys whose value must be nonempty strings.
    for strk in ("title", "slug"):
        if strk not in value:
            continue
        uv = value[strk]
        if not isinstance(uv, str) or not uv:
            return Result.as_failure(
                f"unit metadata {strk!r} must be a nonempty string"
            )

    # Keys whose value must be strings or lists.
    tk = "tags"
    if tk in value:
        uv = value[tk]
        if not isinstance(uv, (str, list)):
            return Result.as_failure(
                f"unit metadata {tk!r} must be a string or a list"
            )

    # Keys whose value must be a datetime object (relies on YAML parser).
    dtk = "pub_time"
    if dtk in value:
        dto = value[dtk]
        if not isinstance(dto, datetime):
            return Result.as_failure(
                f"unit metadata {dtk!r} must be a valid iso8601 timestamp"
            )

    return Result.as_success(value)


class Unit:

    """A single source of text-related content."""

    __slots__ = ("src", "config", "metadata", "raw_text")

    @staticmethod
    def parse_metadata(
        raw: str,
        config: Union["SiteConfig", "SectionConfig"],
        src: Path,
        vfunc: Callable[[dict], Result[dict]] = validate_metadata
    ) -> Result[dict]:
        """Parse the unit metadata into a mapping.

        :param raw: Raw metadata ready for parsing as YAML.
        :param Configuration values.
        :type config: volt.config.SiteConfig or volt.config.SectionConfig.
        :param src: Path to the unit from which the metadata was parsed.
        :param vfunc: Callable for validating the parsed metadata. The callable
            must a accept a single dict value as input and return a
            :class:`Result`.

        :returns: The metadata as a mapping or an error message indicating
            failure.

        """
        try:
            meta = yaml.safe_load(raw) or {}
        except (ScannerError, ParserError):
            return Result.as_failure(f"malformed metadata: {src}")

        vres = vfunc(meta)
        if vres.is_failure:
            return vres

        # Ensure tags is a list of strings.
        tags = meta.get("tags", [])
        if not isinstance(tags, (tuple, list)):
            meta["tags"] = _RE_TAGS.split(str(tags))
        elif tags:
            meta["tags"] = tags

        # Transform pub_time to timezone-aware datetime object.
        if "pub_time" in meta:
            dto = meta["pub_time"]
            if config["timezone"] is not None and dto.tzinfo is None:
                meta["pub_time"] = config["timezone"].localize(dto)

        # Ensure title is supplied.
        if "title" not in meta:
            meta["title"] = src.stem

        if "slug" not in meta:
            # Set slug from title if not supplied.
            meta["slug"] = slugify(meta["title"])
        else:
            # .. or ensure that user supplied values are slugs.
            meta["slug"] = slugify(meta["slug"])

        return Result.as_success(meta)

    @classmethod
    def load(
        cls,
        src: Path,
        config: Union["SiteConfig", "SectionConfig"],
        encoding: str = "utf-8",
    ) -> Result["Unit"]:
        """Create the unit by loading from the given path.

        :param src: Path to the unit source.
        :param Configuration values.
        :param encoding: Name of the unit source encoding.

        :returns: An instance of the unit or an error message indicating
            failure.

        """
        try:
            raw_bytes = src.read_bytes()
        except OSError as e:
            return Result.as_failure(
                "cannot load unit"
                f"{str(src.relative_to(config['pwd']))!r}: {e.strerror}"
            )

        try:
            raw_contents = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            return Result.as_failure(
                "cannot decode unit"
                f" {str(src.relative_to(config['pwd']))!r} using {encoding!r}"
            )
        except LookupError:
            return Result.as_failure(
                "cannot decode unit"
                f" {str(src.relative_to(config['pwd']))!r} using {encoding!r}:"
                " unknown encoding"
            )

        split_contents = _RE_WITH_FM.split(raw_contents, 1)

        try:
            raw_meta, raw_text = split_contents
        except ValueError:
            return Result.as_failure(
                f"malformed unit: {str(src.relative_to(config['pwd']))!r}"
            )

        rmeta = cls.parse_metadata(raw_meta, config, src)
        if rmeta.is_failure:
            return rmeta

        return Result.as_success(cls(src, config, rmeta.data, raw_text))

    def __init__(
        self,
        src: Path,
        config: Union["SiteConfig", "SectionConfig"],
        metadata: dict,
        raw_text: str,
    ) -> None:
        """Initialize the unit.

        :param src: Path to the unit source.
        :param config: Configuration values.
        :param metadata: Unit metadata.
        :param raw_text: Raw text contents of the unit.

        """
        self.src = src
        self.config = config
        self.metadata = metadata
        self.raw_text = raw_text
