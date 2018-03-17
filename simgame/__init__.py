""" Core game module for S.I.M. """
from version import VersionInfo
version = str(VersionInfo.version())
from main import SIMGame as sim_game
GAME_NAME=VersionInfo.name()
