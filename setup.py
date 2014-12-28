#!/usr/bin/env python

from setuptools import setup, find_packages

from volt import __version__


install_requires = [
    "future>=0.14.3",
    "Jinja2>=2.6",
    "Markdown>=2.3.1,<2.5",
]
long_description = open("README.rst").read()

# handle dependencies for python2.x (x < 7)
try:
    __import__("argparse")
except ImportError:
    install_requires.append("argparse")

setup(
    name = "Volt",
    version = __version__,
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
        "syntax highlight": ["pygments>=1.4,<=1.5"],
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
    ]
)
