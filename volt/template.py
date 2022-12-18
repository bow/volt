"""Template functions."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Callable, Optional, ParamSpec, TypeVar

from .constants import TEMPLATE_FILTER_MARK


__all__ = ["filter"]


T = TypeVar("T")
P = ParamSpec("P")


def _make_marker_decorator(
    mark: str,
) -> Callable[
    [Optional[Callable[P, T]], Optional[str]],
    Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]],
]:
    def func(
        __clb: Optional[Callable[P, T]] = None,
        name: Optional[str] = None,
    ) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
        def decorator(clb: Callable[P, T]) -> Callable[P, T]:
            setattr(clb, TEMPLATE_FILTER_MARK, name or clb.__name__)
            return clb

        if __clb is None:
            return decorator

        return decorator(__clb)

    return func


filter = _make_marker_decorator(TEMPLATE_FILTER_MARK)
test = _make_marker_decorator(TEMPLATE_TEST_MARK)
