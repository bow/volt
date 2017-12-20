# -*- coding: utf-8 -*-
"""
    volt.unit
    ~~~~~~~~~

    Unit parsing and writing.

"""
# (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
import re

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


_RE_WITH_FM = re.compile(r"\n---\n+")
_RE_TAGS = re.compile(r",\s+")


class Unit(object):

    """Base class for unit."""

    __slots__ = ("src", "config", "metadata", "raw_text")

    @classmethod
    def parse_metadatata(cls, raw, config, src):
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
    def load(cls, src, config, encoding="utf-8"):
        """Loads the given unit path as an instance of the given unit class."""
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

        rmeta = cls.parse_metadatata(raw_meta, config, src)
        if rmeta.is_failure:
            return rmeta

        return Result.as_success(cls(src, config, rmeta.data, raw_text))

    def __init__(self, src, config, metadata, raw_text):
        self.src = src
        self.config = config
        self.metadata = metadata
        self.raw_text = raw_text
