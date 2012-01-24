"""Collection of useful methods.
"""

import os


def is_valid_root(dir):
    """Returns True if the current directory is a valid volt root directory.

    Checks for 'settings.py' and 'site' directory.
    """
    valid_flags = [os.path.join(dir, x) for x in ['settings.py', 'site']]
    return all([os.path.exists(x) for x in valid_flags])
