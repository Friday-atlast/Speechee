"""
Speechee - Custom Exceptions
All error types for the STT system.
"""


class SpeecheeError(Exception):
    """Base exception for all Speechee errors."""
    pass


class BinaryNotFoundError(SpeecheeError):
    """Raised when whisper.cpp binary is not found."""
    
    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        super().__init__(
            f"Whisper binary not found at: {binary_path}\n"
            f"Please build whisper.cpp first. See: engine/BUILD.md"
        )


class ModelNotFoundError(SpeecheeError):
    """Raised when model file is not found."""
    
    def __init__(self, model_name: str, model_path: str):
        self.model_name = model_name
        self.model_path = model_path
        super().__init__(
            f"Model '{model_name}' not found at: {model_path}\n"
            f"Run: python engine/model_manager.py download --model {model_name}"
        )


class AudioFileError(SpeecheeError):
    """Raised when audio file is invalid or not found."""
    
    def __init__(self, audio_path: str, reason: str = "File not found"):
        self.audio_path = audio_path
        self.reason = reason
        super().__init__(
            f"Audio file error: {reason}\n"
            f"Path: {audio_path}"
        )


class TranscriptionError(SpeecheeError):
    """Raised when transcription process fails."""
    
    def __init__(self, message: str, stderr: str = None):
        self.stderr = stderr
        full_message = f"Transcription failed: {message}"
        if stderr:
            full_message += f"\nDetails: {stderr}"
        super().__init__(full_message)


class UnsupportedFormatError(AudioFileError):
    """Raised when audio format is not supported."""
    
    def __init__(self, audio_path: str, format: str):
        self.format = format
        super().__init__(
            audio_path,
            f"Unsupported audio format: {format}. Supported: wav, mp3, m4a, flac, ogg"
        )