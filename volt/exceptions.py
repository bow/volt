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
class ConfigNotFoundError(Exception):
    """Raised when Volt fails to find voltconf.py."""

# Volt engine warning and exceptions
class EmptyUnitsWarning(RuntimeWarning):
    """Issued when paginations is called without any units to pack in self.units."""
