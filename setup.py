#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

from volt import __author__, __contact__, \
    __homepage__, __version__


with open("README.rst") as src:
    readme = src.read()

with open("CHANGELOG.rst") as src:
    changelog = src.read().replace(".. :changelog:", "").strip()

with open("requirements.txt") as src:
    requirements = [line.strip() for line in src if not line.startswith("-e")]

with open("requirements-dev.txt") as src:
    test_requirements = [line.strip() for line in src]


setup(
    name="Volt",
    version=__version__,
    description="Python static website generator",
    long_description=readme + "\n\n" + changelog,
    author=__author__,
    author_email=__contact__,
    url=__homepage__,
    packages=find_packages(exclude=["*.tests", "*.tests.*",
                                    "tests.*", "tests"]),
    keywords="static website",
    license="BSD",
    include_package_data=True,
    install_requires=requirements,
    tests_require=test_requirements,
    zip_safe=False,
    entry_points="""
    [console_scripts]
    volt=volt.cli:main
    """,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.5",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ]
)
