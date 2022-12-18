"""Template functions."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

from typing import overload, Callable, Optional, ParamSpec, TypeVar

from .constants import TEMPLATE_FILTER_MARK


__all__ = ["filter"]


T = TypeVar("T")
P = ParamSpec("P")


@overload
def filter(__clb: Callable[P, T]) -> Callable[P, T]:
    ...


@overload
def filter(*, name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    ...


def filter(
    __clb: Optional[Callable[P, T]] = None,
    name: Optional[str] = None,
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(clb: Callable[P, T]) -> Callable[P, T]:
        setattr(clb, TEMPLATE_FILTER_MARK, name or clb.__name__)
        return clb

    if __clb is None:
        return decorator

    return decorator(__clb)
