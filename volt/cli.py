# -*- coding: utf-8 -*-
"""
    volt.cli
    ~~~~~~~~

    Main entry point for command line invocation.

    :copyright: (c) 2012-2016 Wibowo Arindrarto <bow@bow.web.id>
    :license: BSD

"""
import click

from . import __version__

__all__ = []


@click.group()
@click.version_option(__version__)
def main():
    """static website generator"""
