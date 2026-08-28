"""Python wrapper for the Deribit API: market data, account management, and trading."""

import logging

from .core import DeribitClient

# Without a handler, logging falls back to logging.lastResort and writes
# warnings and errors to stderr; a library should stay silent until the
# application configures logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["DeribitClient"]
