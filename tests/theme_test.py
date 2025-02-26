"""Tests for volt.theme."""

# Copyright (c) 2012-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from volt.theme import _overlay

# Values to check for overlay test.
_values = (
    1,
    "string",
    True,
    False,
    None,
    [1],
    ["string"],
    [True],
    [{"nested": "yes"}],
)


# TODO: Add more descriptive test case names.
@pytest.mark.parametrize(
    "base, mod, expected",
    [
        (None, {}, {}),
        ({}, None, {}),
        (None, None, {}),
        ({}, {}, {}),
        (None, {"a": 1, "b": {"bb": "x"}}, {"a": 1, "b": {"bb": "x"}}),
        ({"a": 1, "b": {"bb": "x"}}, None, {"a": 1, "b": {"bb": "x"}}),
        *[({"a": v}, {}, {"a": v}) for v in _values],
        *[({}, {"a": v}, {"a": v}) for v in _values],
        *[({"a": "init"}, {"a": v}, {"a": v}) for v in _values],
        *[
            (
                {"a": "init", "b": {"other": "x"}},
                {"a": v},
                {"a": v, "b": {"other": "x"}},
            )
            for v in _values
        ],
        *[
            (
                {"a": {"foo": {"bar": "baz"}}, "b": {"other": "x"}},
                {"a": v},
                {"a": v, "b": {"other": "x"}},
            )
            for v in _values
        ],
        *[
            (
                {"a": v},
                {"a": "mod", "b": {"other": "x"}},
                {"a": "mod", "b": {"other": "x"}},
            )
            for v in _values
        ],
        *[
            (
                {"a": v},
                {"a": {"foo": {"bar": "baz"}}, "b": {"other": "x"}},
                {"a": {"foo": {"bar": "baz"}}, "b": {"other": "x"}},
            )
            for v in _values
        ],
        # Complex, realistic example.
        (
            {
                "opts": {"nav": ["x", "y", "z"], "items": [{"value": 1}, {"value": 5}]},
                "hooks": {
                    "h1": {
                        "enabled": False,
                        "color": "hex",
                    },
                    "h2": {
                        "enabled": True,
                    },
                },
                "others": {
                    "flat": 123,
                },
            },
            {
                "opts": {
                    "nav": ["a", "b", "c"],
                    "year": 2022,
                },
                "hooks": {
                    "h1": {
                        "enabled": True,
                        "gradient": "v1",
                    },
                },
                "others": {"deeply": [{"nested": True}]},
            },
            {
                "opts": {
                    "nav": ["a", "b", "c"],
                    "year": 2022,
                    "items": [{"value": 1}, {"value": 5}],
                },
                "hooks": {
                    "h1": {
                        "enabled": True,
                        "color": "hex",
                        "gradient": "v1",
                    },
                    "h2": {
                        "enabled": True,
                    },
                },
                "others": {
                    "deeply": [{"nested": True}],
                    "flat": 123,
                },
            },
        ),
    ],
)
def test__overlay(base, mod, expected):
    observed = _overlay(base, mod)
    assert expected == observed
