#!/usr/bin/env python

import distribute_setup
distribute_setup.use_setuptools()

import sys
from setuptools import setup, find_packages

from volt import VERSION


install_requires = [
    "Jinja2>=2.6",
    "Markdown>=2.1.1",
]
version = VERSION
long_description = open("README.rst").read()

# handle python 3
extra = dict()
if sys.version_info >= (3,):
    extra['use_2to3'] = True

# handle dependencies for python2.x (x < 7)
try:
    __import__("argparse")
except ImportError:
    install_requires.append("argparse")

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
    install_requires = install_requires,
    extras_require = {
        "rst": ["docutils>=0.8.1"],
        "textile": ["textile>=2.1.5"],
        "fast markdown": ["discount>=0.2.1"],
        "syntax highlight": ["pygments>=1.4"],
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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
    **extra
)
