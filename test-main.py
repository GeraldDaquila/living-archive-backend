"""Constitutional TEST application entrypoint.

This module deliberately re-exports the validated ASGI application from main.py.
TEST and production therefore exercise the same application graph while remaining
separate deployment targets.
"""

from main import app

__all__ = ["app"]
