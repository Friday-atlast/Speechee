"""
Speechee STT Package
Speech-to-Text transcription using whisper.cpp
"""

from .offline import OfflineTranscriber
from .live_stt import LiveSTT, LiveSTTResult
from .formatter import OutputFormatter, TranscriptSegment
from .output_manager import OutputManager, SavedTranscript
from .exceptions import (
    SpeecheeError,
    ModelNotFoundError,
    AudioFileError,
    TranscriptionError,
    BinaryNotFoundError
)

__all__ = [
    # Transcribers
    "OfflineTranscriber",
    "LiveSTT",
    "LiveSTTResult",
    
    # Output
    "OutputFormatter",
    "TranscriptSegment",
    "OutputManager",
    "SavedTranscript",
    
    # Exceptions
    "SpeecheeError",
    "ModelNotFoundError",
    "AudioFileError",
    "TranscriptionError",
    "BinaryNotFoundError"
]

__version__ = "1.0.0-dev"