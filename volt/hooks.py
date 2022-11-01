"""Hooks for various events."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from . import signals as s


__all__ = [
    "post_site_load_engines",
    "post_site_collect_targets",
]


post_site_load_engines = s.post_site_load_engines.connect
post_site_collect_targets = s.post_site_collect_targets.connect
pre_site_write = s.pre_site_write.connect
