"""
Speechee STT Package
Speech-to-Text transcription using whisper.cpp
"""

from .offline import OfflineTranscriber
from .live_stt import LiveSTT, LiveSTTResult  
from .exceptions import (
    SpeecheeError,
    ModelNotFoundError,
    AudioFileError,
    TranscriptionError,
    BinaryNotFoundError
)

__all__ = [
    "OfflineTranscriber",
    "LiveSTT",              
    "LiveSTTResult",        
    "SpeecheeError",
    "ModelNotFoundError",
    "AudioFileError",
    "TranscriptionError",
    "BinaryNotFoundError"
]

__version__ = "1.0.0-dev"