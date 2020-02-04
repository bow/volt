# -*- coding: utf-8 -*-
"""
    volt
    ~~~~

    A versatile static website generator.

    :copyright: (c) 2012-2017 Wibowo Arindrarto <bow@bow.web.id>
    :license: BSD

"""
NAME = "volt"

__author__ = "Wibowo Arindrarto"
__contact__ = "bow@bow.web.id"
__homepage__ = "https://github.com/bow/volt"

from ._version import get_versions  # type: ignore

__version__ = get_versions()["version"]
del get_versions
