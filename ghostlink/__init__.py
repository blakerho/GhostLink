"""ghostlink package.

This package exposes encoding and decoding helpers as well as the
``main`` function used by the ``ghostlink`` console script.
"""

from .__main__ import *  # noqa: F401,F403
from .profiles import freq_profile

__all__ = [name for name in globals() if not name.startswith('_')]
