# from importlib.metadata import PackageNotFoundError, version
#
# try:
#     __version__ = version(__name__)
# except PackageNotFoundError:
#     # package is not installed
#     pass
from ._version import version as __version__
