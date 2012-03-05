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
    description = "The static website generator with potential",
    long_description = long_description,
    author = "Wibowo Arindrarto",
    author_email = "bow@bow.web.id",
    url = "http://github.com/bow/volt/",
    keywords = "static website",
    license = "BSD",
    packages = find_packages(),
    include_package_data = True,
    install_requires = [
        "Jinja2>=2.6",
        "PyYAML>=3.10",
        "Markdown>=2.1.1",
        "pygments>=1.4",
    ],
    extras_require = {
        "fast markdown": ["discount>=0.2.1"],
    },
    test_suite='nose.collector',
    tests_require=[
        'nose>=1.1.2',
        'mock>=0.8.0',
    ],
    zip_safe = False,
    entry_points = """
    [console_scripts]
    volt = volt.main:main
    """,
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
)
