"""
Speechee Config Package
Configuration management system.
"""

from .settings import Settings, get_settings, get_config_value

__all__ = ["Settings", "get_settings", "get_config_value"]
__version__ = "1.0.0-dev"