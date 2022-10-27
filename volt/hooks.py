"""Hooks for various events."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from . import signals as s


__all__ = ["post_collect_targets"]


post_collect_targets = s.post_collect_targets.connect
