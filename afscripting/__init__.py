"""afscripting
"""

__author__      = "Joel Dubowy"

__version_info__ = (1,1,0)
__version__ = '.'.join([str(n) for n in __version_info__])

try:
    from . import args, options, utils
except:
    # This should only happen when __version__ is being
    # imported in setup.py, so just ignore
    pass