""" Core game module for S.I.M. """
from .version import VersionInfo as version
VERSION = str('.'.join([str(n) for n in version.version()]))
GAME_NAME=version.name()
