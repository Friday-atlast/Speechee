"""
Speechee Audio Package
Microphone capture and audio processing utilities.
"""

from .mic import Microphone
from .recorder import AudioRecorder
from .preprocess import AudioPreprocessor

__all__ = [
    "Microphone",
    "AudioRecorder", 
    "AudioPreprocessor"
]

__version__ = "1.0.0-dev" 
