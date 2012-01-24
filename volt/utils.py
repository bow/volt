"""Collection of useful methods.
"""

import os


def is_valid_volt(dir):
    """Returns True if the current directory is a valid Volt directory.

    Checks for 'settings.py' and 'site' directory.
    """
    valid_flags = [os.path.join(dir, x) for x in ['settings.py', 'site']]
    return all(map(os.path.exists, valid_flags))
