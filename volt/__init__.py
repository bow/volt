"""
----
volt
----

The Python static website generator

:copyright: (c) 2012-2013 Wibowo Arindrarto <bow@bow.web.id>

"""

# The versioning scheme here tries to follow the Semantic Versioning
# Specification (http://www.semver.org)
#
# Additionally, a '-dev' suffix is appended for all non-release version.

RELEASE = False

__version_info__ = ('0', '4', '0')
__version__ = '.'.join(__version_info__)
__version__ += '-dev' if not RELEASE else ''

__author__ = 'Wibowo Arindrarto'
__contact__ = 'bow@bow.web.id'
__homepage__ = 'http://github.com/bow/volt'
