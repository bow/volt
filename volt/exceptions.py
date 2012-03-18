# -*- coding: utf-8 -*-
"""
---------------
volt.exceptions
---------------

Volt exception classes.

:copyright: (c) 2012 Wibowo Arindrarto <bow@bow.web.id>
:license: BSD

"""


# Volt config exceptions
class ConfigError(Exception):
    """Raised for errors related to configurations."""
    pass

class ConfigNotFoundError(Exception):
    """Raised when Volt fails to find voltconf.py."""
    pass


# Volt engine warning and exceptions
class EmptyUnitsWarning(RuntimeWarning):
    """Issued when build_packs is called without any units to pack in self.units."""
    pass

class DuplicateOutputError(Exception):
    """Raised when Volt tries to overwrite an existing HTML output file.

    This is an exception because in a normal Volt run, there should be no
    duplicate output file. Each unit and pack should have its own unique
    absolute path.

    """
    pass

class ContentError(Exception):
    """Base exception for content-related error."""
    pass

class HeaderFieldError(ContentError):
    """Raised for unit header-related error."""
    pass

class PermalinkTemplateError(ContentError):
    """Raised if a header field value defined in the permalink template is not found."""
    pass

class ParseError(ContentError):
    """Raised if a content-parsing related error occurs."""
    pass
