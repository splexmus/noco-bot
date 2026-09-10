"""Compatibility entry point for the robot-side image API.

The importable application lives in the ``client.api`` package. Run it with:
``uvicorn client.api:app --host 0.0.0.0 --port 8001``.
"""

from client.api import app

__all__ = ["app"]
