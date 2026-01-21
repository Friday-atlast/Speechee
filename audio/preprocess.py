"""
Speechee - Audio Preprocessor
Audio normalization and format conversion utilities.
"""

import os
import wave
import struct
from pathlib import Path
from typing import Optional, Union, Tuple
from dataclasses import dataclass

import numpy as np

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    sf = None
    HAS_SOUNDFILE = False


@dataclass
class AudioInfo:
    """Audio file information."""
    filepath: str
    sample_rate: int
    channels: int
    duration_sec: float
    format: str
    bit_depth: int
    file_size_bytes: int


class AudioPreprocessor:
    """
    Audio preprocessing utilities.
    
    Usage:
        processor = AudioPreprocessor()
        info = processor.get_info("audio.wav")
        processor.normalize("audio.wav", "normalized.wav")
        processor.convert_to_whisper_format("audio.mp3", "audio_16k.wav")
    """
    
    # Whisper.cpp required format
    TARGET_SAMPLE_RATE = 16000
    TARGET_CHANNELS = 1
    TARGET_BIT_DEPTH = 16
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.webm'}
    
    def __init__(self):
        """Initialize preprocessor."""
        pass
    
    def get_info(self, audio_path: Union[str, Path]) -> AudioInfo:
        """
        Get audio file information.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioInfo object
        """
        path = Path(audio_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        
        file_size = path.stat().st_size
        suffix = path.suffix.lower()
        
        if suffix == '.wav':
            return self._get_wav_info(path, file_size)
        elif HAS_SOUNDFILE:
            return self._get_soundfile_info(path, file_size)
        else:
            raise ValueError(f"Cannot read format {suffix}. Install soundfile: pip install soundfile")
    
    def _get_wav_info(self, path: Path, file_size: int) -> AudioInfo:
        """Get WAV file info using wave module."""
        with wave.open(str(path), 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.getnframes()
            bit_depth = wf.getsampwidth() * 8
            duration = frames / sample_rate
        
        return AudioInfo(
            filepath=str(path),
            sample_rate=sample_rate,
            channels=channels,
            duration_sec=round(duration, 2),
            format='wav',
            bit_depth=bit_depth,
            file_size_bytes=file_size
        )
    
    def _get_soundfile_info(self, path: Path, file_size: int) -> AudioInfo:
        """Get audio info using soundfile."""
        info = sf.info(str(path))
        
        return AudioInfo(
            filepath=str(path),
            sample_rate=info.samplerate,
            channels=info.channels,
            duration_sec=round(info.duration, 2),
            format=info.format,
            bit_depth=info.subtype_info.split()[0] if info.subtype_info else 16,
            file_size_bytes=file_size
        )
    
    def is_whisper_compatible(self, audio_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Check if audio is compatible with Whisper.
        
        Returns:
            (is_compatible, reason)
        """
        try:
            info = self.get_info(audio_path)
        except Exception as e:
            return False, str(e)
        
        issues = []
        
        if info.sample_rate != self.TARGET_SAMPLE_RATE:
            issues.append(f"Sample rate: {info.sample_rate} (need {self.TARGET_SAMPLE_RATE})")
        
        if info.channels != self.TARGET_CHANNELS:
            issues.append(f"Channels: {info.channels} (need {self.TARGET_CHANNELS})")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "Compatible"
    
    def normalize_volume(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path] = None,
        target_db: float = -20.0
    ) -> str:
        """
        Normalize audio volume.
        
        Args:
            input_path: Input audio file
            output_path: Output file. None = overwrite input
            target_db: Target volume in dB
            
        Returns:
            Output file path
        """
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else input_path
        
        if not HAS_SOUNDFILE:
            raise ImportError("soundfile required: pip install soundfile")
        
        # Read audio
        data, sample_rate = sf.read(str(input_path))
        
        # Calculate current RMS
        rms = np.sqrt(np.mean(data ** 2))
        current_db = 20 * np.log10(rms) if rms > 0 else -100
        
        # Calculate gain
        gain_db = target_db - current_db
        gain = 10 ** (gain_db / 20)
        
        # Apply gain
        normalized = data * gain
        
        # Clip to prevent distortion
        normalized = np.clip(normalized, -1.0, 1.0)
        
        # Save
        sf.write(str(output_path), normalized, sample_rate)
        
        return str(output_path)
    
    def convert_to_whisper_format(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path] = None
    ) -> str:
        """
        Convert audio to Whisper-compatible format (16kHz, mono, 16-bit WAV).
        
        Args:
            input_path: Input audio file
            output_path: Output WAV file. None = auto-generate
            
        Returns:
            Output file path
        """
        input_path = Path(input_path)
        
        if output_path is None:
            output_path = input_path.with_suffix('.16k.wav')
        else:
            output_path = Path(output_path)
        
        if not HAS_SOUNDFILE:
            raise ImportError("soundfile required: pip install soundfile")
        
        # Read audio
        data, original_sr = sf.read(str(input_path))
        
        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Resample if needed
        if original_sr != self.TARGET_SAMPLE_RATE:
            # Simple resampling using numpy
            duration = len(data) / original_sr
            new_length = int(duration * self.TARGET_SAMPLE_RATE)
            indices = np.linspace(0, len(data) - 1, new_length)
            data = np.interp(indices, np.arange(len(data)), data)
        
        # Convert to 16-bit integer
        data = (data * 32767).astype(np.int16)
        
        # Save as WAV
        sf.write(str(output_path), data, self.TARGET_SAMPLE_RATE, subtype='PCM_16')
        
        return str(output_path)
    
    def trim_silence(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path] = None,
        threshold_db: float = -40.0,
        min_silence_sec: float = 0.5
    ) -> str:
        """
        Trim silence from beginning and end of audio.
        
        Args:
            input_path: Input audio file
            output_path: Output file
            threshold_db: Volume threshold for silence
            min_silence_sec: Minimum silence duration to trim
            
        Returns:
            Output file path
        """
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else input_path.with_suffix('.trimmed.wav')
        
        if not HAS_SOUNDFILE:
            raise ImportError("soundfile required: pip install soundfile")
        
        # Read audio
        data, sample_rate = sf.read(str(input_path))
        
        # Convert threshold
        threshold = 10 ** (threshold_db / 20)
        
        # Find non-silent regions
        if len(data.shape) > 1:
            amplitude = np.abs(data).max(axis=1)
        else:
            amplitude = np.abs(data)
        
        non_silent = amplitude > threshold
        
        # Find start and end
        non_silent_indices = np.where(non_silent)[0]
        
        if len(non_silent_indices) == 0:
            # All silence
            sf.write(str(output_path), data, sample_rate)
            return str(output_path)
        
        start = non_silent_indices[0]
        end = non_silent_indices[-1] + 1
        
        # Trim
        trimmed = data[start:end]
        
        # Save
        sf.write(str(output_path), trimmed, sample_rate)
        
        return str(output_path)


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Audio Preprocessor")
    subparsers = parser.add_subparsers(dest="command")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get audio info")
    info_parser.add_argument("file", help="Audio file path")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check Whisper compatibility")
    check_parser.add_argument("file", help="Audio file path")
    
    # Convert command
    conv_parser = subparsers.add_parser("convert", help="Convert to Whisper format")
    conv_parser.add_argument("input", help="Input file")
    conv_parser.add_argument("--output", "-o", help="Output file")
    
    # Normalize command
    norm_parser = subparsers.add_parser("normalize", help="Normalize volume")
    norm_parser.add_argument("input", help="Input file")
    norm_parser.add_argument("--output", "-o", help="Output file")
    norm_parser.add_argument("--db", type=float, default=-20.0, help="Target dB")
    
    args = parser.parse_args()
    processor = AudioPreprocessor()
    
    if args.command == "info":
        info = processor.get_info(args.file)
        print("\n" + "=" * 50)
        print("AUDIO INFO")
        print("=" * 50)
        print(f"  File: {info.filepath}")
        print(f"  Duration: {info.duration_sec}s")
        print(f"  Sample Rate: {info.sample_rate} Hz")
        print(f"  Channels: {info.channels}")
        print(f"  Format: {info.format}")
        print(f"  Bit Depth: {info.bit_depth}")
        print(f"  Size: {info.file_size_bytes / 1024:.1f} KB")
        print("=" * 50)
    
    elif args.command == "check":
        compatible, reason = processor.is_whisper_compatible(args.file)
        if compatible:
            print(f"\n✓ {args.file} is Whisper compatible!")
        else:
            print(f"\n✗ Not compatible: {reason}")
    
    elif args.command == "convert":
        output = processor.convert_to_whisper_format(args.input, args.output)
        print(f"\n✓ Converted: {output}")
    
    elif args.command == "normalize":
        output = processor.normalize_volume(args.input, args.output, args.db)
        print(f"\n✓ Normalized: {output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()