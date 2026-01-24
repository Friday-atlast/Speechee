"""
Speechee - Offline Transcriber
Python wrapper for whisper.cpp using subprocess.
FIXED: Language parameter properly passed to whisper-cli
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.config import EngineConfig

try:
    from .exceptions import (
        BinaryNotFoundError,
        ModelNotFoundError,
        AudioFileError,
        TranscriptionError,
        UnsupportedFormatError
    )
except ImportError:
    from exceptions import (
        BinaryNotFoundError,
        ModelNotFoundError,
        AudioFileError,
        TranscriptionError,
        UnsupportedFormatError
    )


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""
    text: str
    language: str
    model: str
    audio_path: str
    duration_ms: Optional[float] = None
    segments: Optional[list] = None
    success: bool = True
    error: Optional[str] = None
    processing_time_sec: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "text": self.text,
            "language": self.language,
            "model": self.model,
            "audio_path": self.audio_path,
            "duration_ms": self.duration_ms,
            "segments": self.segments,
            "success": self.success,
            "error": self.error,
            "processing_time_sec": self.processing_time_sec
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class OfflineTranscriber:
    """
    Offline Speech-to-Text transcriber using whisper.cpp.
    
    IMPORTANT: This class TRANSCRIBES audio, it does NOT translate.
    Hindi audio will output Hindi text (Devanagari).
    English audio will output English text.
    
    Usage:
        transcriber = OfflineTranscriber(model="tiny.en")
        result = transcriber.transcribe("audio.wav")
        print(result.text)
    """
    
    SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
    
    # Language code mapping for whisper
    LANGUAGE_CODES = {
        "auto": "auto",
        "en": "en", "english": "en",
        "hi": "hi", "hindi": "hi",
        "es": "es", "spanish": "es",
        "fr": "fr", "french": "fr",
        "de": "de", "german": "de",
        "ja": "ja", "japanese": "ja",
        "ko": "ko", "korean": "ko",
        "zh": "zh", "chinese": "zh",
        "ar": "ar", "arabic": "ar",
        "ru": "ru", "russian": "ru",
        "pt": "pt", "portuguese": "pt",
        "it": "it", "italian": "it",
        "nl": "nl", "dutch": "nl",
        "pl": "pl", "polish": "pl",
        "tr": "tr", "turkish": "tr",
        "ta": "ta", "tamil": "ta",
        "te": "te", "telugu": "te",
        "mr": "mr", "marathi": "mr",
        "bn": "bn", "bengali": "bn",
        "gu": "gu", "gujarati": "gu",
        "kn": "kn", "kannada": "kn",
        "ml": "ml", "malayalam": "ml",
        "pa": "pa", "punjabi": "pa",
        "ur": "ur", "urdu": "ur",
    }
    
    def __init__(
        self,
        model: str = None,
        language: str = "auto",
        threads: int = None,
        translate: bool = False,
        verbose: bool = False
    ):
        """
        Initialize transcriber.
        
        Args:
            model: Model name (tiny.en, tiny, base, small). Default from config.
            language: Language code ("hi" for Hindi, "en" for English, "auto" for auto-detect)
            threads: CPU threads. None = auto (uses config value)
            translate: If True, translates to English. Default FALSE = transcribe in original language
            verbose: Print debug info. Default False.
        """
        self.config = EngineConfig
        
        # Get defaults from config
        try:
            from config import get_settings
            settings = get_settings()
            default_model = settings.get("stt.model", "tiny.en")
            default_threads = settings.get("stt.threads", 4)
        except:
            default_model = self.config.DEFAULT_MODEL
            default_threads = 4
        
        self.model = model or default_model
        self.language = self._normalize_language(language)
        self.threads = threads or default_threads
        self.translate = translate
        self.verbose = verbose
        
        # Validate setup
        self._validate_binary()
        self._validate_model()
        
        if self.verbose:
            print(f"[TRANSCRIBER] Initialized:")
            print(f"  Model: {self.model}")
            print(f"  Language: {self.language}")
            print(f"  Threads: {self.threads}")
            print(f"  Translate: {self.translate}")
    
    def _normalize_language(self, lang: str) -> str:
        """Normalize language code."""
        if not lang:
            return "auto"
        lang = lang.lower().strip()
        return self.LANGUAGE_CODES.get(lang, lang)
    
    def _validate_binary(self) -> None:
        """Check if whisper.cpp binary exists."""
        binary_path = self.config.WHISPER_BINARY
        if not binary_path.exists():
            raise BinaryNotFoundError(str(binary_path))
    
    def _validate_model(self) -> None:
        """Check if model file exists."""
        if not self.config.is_model_downloaded(self.model):
            model_path = self.config.get_model_path(self.model)
            raise ModelNotFoundError(self.model, str(model_path))
    
    def _validate_audio(self, audio_path: Union[str, Path]) -> Path:
        """
        Validate audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Resolved Path object
            
        Raises:
            AudioFileError: If file doesn't exist
            UnsupportedFormatError: If format not supported
        """
        path = Path(audio_path).resolve()
        
        # Check existence
        if not path.exists():
            raise AudioFileError(str(path), "File not found")
        
        # Check if it's a file
        if not path.is_file():
            raise AudioFileError(str(path), "Not a file")
        
        # Check format
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(str(path), suffix)
        
        # Check file size (not empty)
        if path.stat().st_size == 0:
            raise AudioFileError(str(path), "File is empty")
        
        return path
    
    def _build_command(self, audio_path: Path, output_format: str = "txt") -> list:
        """
        Build whisper.cpp command with correct parameters.
        
        CRITICAL: We use transcribe mode, NOT translate mode by default.
        This ensures Hindi audio outputs Hindi text, not English translation.
        
        Args:
            audio_path: Path to audio file
            output_format: Output format (txt, json, srt)
            
        Returns:
            Command as list of strings
        """
        binary = str(self.config.WHISPER_BINARY)
        model_path = str(self.config.get_model_path(self.model))
        
        cmd = [
            binary,
            "-m", model_path,
            "-f", str(audio_path),
            "-t", str(self.threads),
            "--no-timestamps",  # Cleaner output
        ]
        
        # Language parameter
        # If language is specified (not auto), explicitly set it
        if self.language and self.language != "auto":
            cmd.extend(["-l", self.language])
            if self.verbose:
                print(f"[CMD] Setting language: {self.language}")
        
        # Translate flag
        # Only add if user explicitly wants translation to English
        # By default, we TRANSCRIBE (keep original language)
        if self.translate:
            cmd.append("--translate")
            if self.verbose:
                print(f"[CMD] Translation mode enabled (output will be English)")
        else:
            if self.verbose:
                print(f"[CMD] Transcription mode (output in original language)")
        
        # Output format
        if output_format == "json":
            cmd.append("-oj")
        elif output_format == "srt":
            cmd.append("-osrt")
        else:
            cmd.append("-otxt")
        
        return cmd
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        output_format: str = "txt",
        save_output: bool = False,
        output_dir: Union[str, Path] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        IMPORTANT: This TRANSCRIBES audio in its original language.
        - Hindi audio → Hindi text (Devanagari)
        - English audio → English text
        - Hinglish audio → Mixed text
        
        Args:
            audio_path: Path to audio file
            output_format: Output format (txt, json, srt)
            save_output: Save transcription to file
            output_dir: Directory for output files
            
        Returns:
            TranscriptionResult object
        """
        start_time = time.time()
        
        # Validate audio file
        audio_path = self._validate_audio(audio_path)
        
        if self.verbose:
            print(f"\n[TRANSCRIBE] {audio_path.name}")
            print(f"  Model: {self.model}")
            print(f"  Language: {self.language}")
            print(f"  Translate: {self.translate}")
            print(f"  Threads: {self.threads}")
        
        # Build command
        cmd = self._build_command(audio_path, output_format)
        
        if self.verbose:
            print(f"  Command: {' '.join(cmd)}")
        
        try:
            # Run whisper.cpp
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=str(audio_path.parent),
                encoding='utf-8',
                errors='replace'
            )
            
            processing_time = time.time() - start_time
            
            # Check for errors
            if process.returncode != 0:
                error_msg = process.stderr or process.stdout or "Unknown error"
                raise TranscriptionError(
                    f"Process exited with code {process.returncode}",
                    error_msg
                )
            
            # Read output file
            output_suffix = {"txt": ".txt", "json": ".json", "srt": ".srt"}
            output_file = audio_path.with_suffix(
                audio_path.suffix + output_suffix.get(output_format, ".txt")
            )
            
            if not output_file.exists():
                # Try alternate naming
                output_file = Path(str(audio_path) + output_suffix.get(output_format, ".txt"))
            
            if output_file.exists():
                text = output_file.read_text(encoding="utf-8").strip()
                
                # Clean up output file if not saving
                if not save_output:
                    output_file.unlink()
            else:
                # Fallback: try to get text from stdout
                text = process.stdout.strip()
                if not text:
                    raise TranscriptionError("No output generated")
            
            # Handle save_output
            if save_output and output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                save_path = output_dir / f"{audio_path.stem}_transcript.{output_format}"
                save_path.write_text(text, encoding="utf-8")
                if self.verbose:
                    print(f"  Saved: {save_path}")
            
            # Parse JSON if needed
            segments = None
            if output_format == "json" and text:
                try:
                    json_data = json.loads(text)
                    segments = json_data.get("transcription", [])
                    # Extract plain text from segments
                    if segments:
                        text = " ".join([s.get("text", "") for s in segments]).strip()
                except json.JSONDecodeError:
                    pass
            
            result = TranscriptionResult(
                text=text,
                language=self.language,
                model=self.model,
                audio_path=str(audio_path),
                segments=segments,
                success=True,
                processing_time_sec=round(processing_time, 2)
            )
            
            if self.verbose:
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"  Result: {preview}")
                print(f"  Time: {processing_time:.2f}s")
            
            return result
            
        except subprocess.TimeoutExpired:
            raise TranscriptionError("Process timed out (>10 minutes)")
        except FileNotFoundError:
            raise BinaryNotFoundError(str(self.config.WHISPER_BINARY))
        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(str(e))
    
    def transcribe_hindi(self, audio_path: Union[str, Path]) -> TranscriptionResult:
        """
        Convenience method for Hindi transcription.
        Ensures output is in Hindi (Devanagari), not translated to English.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            TranscriptionResult with Hindi text
        """
        self.language = "hi"
        self.translate = False
        return self.transcribe(audio_path)
    
    def transcribe_multiple(
        self,
        audio_paths: list,
        output_format: str = "txt"
    ) -> list:
        """
        Transcribe multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            output_format: Output format
            
        Returns:
            List of TranscriptionResult objects
        """
        results = []
        total = len(audio_paths)
        
        for i, audio_path in enumerate(audio_paths, 1):
            print(f"[{i}/{total}] Processing: {Path(audio_path).name}")
            
            try:
                result = self.transcribe(audio_path, output_format)
                results.append(result)
            except Exception as e:
                # Create error result
                results.append(TranscriptionResult(
                    text="",
                    language=self.language,
                    model=self.model,
                    audio_path=str(audio_path),
                    success=False,
                    error=str(e)
                ))
                print(f"  Error: {e}")
        
        return results
    
    def get_info(self) -> Dict[str, Any]:
        """Get transcriber configuration info."""
        return {
            "model": self.model,
            "language": self.language,
            "threads": self.threads,
            "translate": self.translate,
            "binary": str(self.config.WHISPER_BINARY),
            "binary_exists": self.config.WHISPER_BINARY.exists(),
            "model_path": str(self.config.get_model_path(self.model)),
            "model_exists": self.config.is_model_downloaded(self.model),
            "supported_formats": list(self.SUPPORTED_FORMATS),
            "supported_languages": list(self.LANGUAGE_CODES.keys())
        }


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface for offline transcription."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Offline Transcriber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe English audio
  python offline.py transcribe audio.wav
  
  # Transcribe Hindi audio (output in Devanagari)
  python offline.py transcribe hindi.wav --language hi
  
  # Auto-detect language
  python offline.py transcribe audio.wav --language auto
  
  # Translate to English (converts any language to English)
  python offline.py transcribe hindi.wav --translate
  
  # Use specific model
  python offline.py transcribe audio.wav --model base
  
  # Save output to file
  python offline.py transcribe audio.wav --save
  
  # JSON output format
  python offline.py transcribe audio.wav --output json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Transcribe command
    trans_parser = subparsers.add_parser("transcribe", help="Transcribe audio file")
    trans_parser.add_argument("audio", help="Path to audio file")
    trans_parser.add_argument("--model", "-m", default="tiny.en", help="Model name (default: tiny.en)")
    trans_parser.add_argument("--language", "-l", default="auto", help="Language code: hi, en, auto (default: auto)")
    trans_parser.add_argument("--translate", action="store_true", help="Translate to English (default: transcribe in original language)")
    trans_parser.add_argument("--output", "-o", choices=["txt", "json", "srt"], default="txt", help="Output format")
    trans_parser.add_argument("--threads", "-t", type=int, default=4, help="CPU threads (default: 4)")
    trans_parser.add_argument("--save", "-s", action="store_true", help="Save output to file")
    trans_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show transcriber info")
    info_parser.add_argument("--model", "-m", default="tiny.en", help="Model to check")
    
    args = parser.parse_args()
    
    if args.command == "transcribe":
        try:
            transcriber = OfflineTranscriber(
                model=args.model,
                language=args.language,
                threads=args.threads,
                translate=args.translate,
                verbose=args.verbose
            )
            
            result = transcriber.transcribe(
                args.audio,
                output_format=args.output,
                save_output=args.save,
                output_dir="output/transcripts" if args.save else None
            )
            
            if args.output == "json":
                print(result.to_json())
            else:
                print(f"\n{'='*60}")
                print("TRANSCRIPTION RESULT")
                print('='*60)
                print(f"\n{result.text}\n")
                print('='*60)
                print(f"Language: {result.language}")
                print(f"Model: {result.model}")
                if result.processing_time_sec:
                    print(f"Time: {result.processing_time_sec}s")
                print('='*60)
                
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    
    elif args.command == "info":
        try:
            transcriber = OfflineTranscriber(model=args.model)
            info = transcriber.get_info()
            
            print(f"\n{'='*60}")
            print("TRANSCRIBER INFO")
            print('='*60)
            for key, value in info.items():
                print(f"  {key}: {value}")
            print('='*60)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()