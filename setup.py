#!/usr/bin/env python

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

from volt import __version__


version = __version__
long_description = open("README.rst").read()

setup(
    name = "Volt",
    version = version,
    description = "Volt is a static website generator with extra features.",
    long_description = long_description,
    author = "Wibowo Arindrarto",
    author_email = "bow@bow.web.id",
    url = "",
    license = "BSD",
    packages = find_packages(),
    install_requires = [
        "pyyaml", 
        "markdown", 
        "jinja2"
    ],
    # test_suite,
    # tests_require,
    zip_safe = False,
    entry_points = """
    [console_scripts]
    volt = volt.main:main
    """,
)
