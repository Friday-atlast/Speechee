"""
Speechee API Package
REST API layer for Speech-to-Text service.
"""

from .server import app
from .routes import router

__all__ = ["app", "router"]
__version__ = "1.0.0-dev"