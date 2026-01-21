"""
Speechee Engine Package
Offline-first STT engine using whisper.cpp
"""

from .config import EngineConfig
from .model_manager import ModelManager

__all__ = ["EngineConfig", "ModelManager"]
__version__ = "1.0.0-dev"