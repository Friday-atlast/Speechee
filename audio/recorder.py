"""
Speechee - Audio Recorder
Record audio from microphone and save to WAV file.
"""

import os
import sys
import time
import wave
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
from dataclasses import dataclass

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_BACKEND = "sounddevice"
except ImportError:
    sd = None
    sf = None
    AUDIO_BACKEND = None

try:
    import pyaudio
    if AUDIO_BACKEND is None:
        AUDIO_BACKEND = "pyaudio"
except ImportError:
    pyaudio = None

try:
    from .mic import Microphone, MicrophoneError
except ImportError:
    from mic import Microphone, MicrophoneError


@dataclass
class RecordingResult:
    """Result of a recording operation."""
    filepath: str
    duration_sec: float
    sample_rate: int
    channels: int
    file_size_bytes: int
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "filepath": self.filepath,
            "duration_sec": self.duration_sec,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "file_size_bytes": self.file_size_bytes,
            "success": self.success,
            "error": self.error
        }


class AudioRecorder:
    """
    Audio recorder for capturing microphone input.
    
    Usage:
        recorder = AudioRecorder()
        result = recorder.record(duration=5)
        print(result.filepath)  # output/temp/recording_xxxxx.wav
    """
    
    def __init__(
        self,
        output_dir: Union[str, Path] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        device_id: Optional[int] = None
    ):
        """
        Initialize recorder.
        
        Args:
            output_dir: Directory for recordings. Default: output/temp
            sample_rate: Sample rate in Hz. Default: 16000 (Whisper requirement)
            channels: Number of channels. Default: 1 (mono)
            device_id: Specific input device. Default: system default
        """
        # Set output directory
        if output_dir is None:
            # Get project root
            project_root = Path(__file__).parent.parent
            output_dir = project_root / "output" / "temp"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio settings
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id = device_id
        
        # Initialize microphone
        self.mic = Microphone(device_id)
    
    def _generate_filename(self, prefix: str = "recording") -> Path:
        """Generate unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.wav"
        return self.output_dir / filename
    
    def record(
        self,
        duration: float = 5.0,
        filename: Optional[str] = None,
        show_progress: bool = True
    ) -> RecordingResult:
        """
        Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            filename: Custom filename. None = auto-generate
            show_progress: Show recording progress
            
        Returns:
            RecordingResult object
        """
        # Determine output path
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._generate_filename()
        
        if show_progress:
            print(f"\n[RECORDING] Duration: {duration}s")
            print(f"  Output: {filepath}")
            print(f"  Sample Rate: {self.sample_rate} Hz")
            print(f"  Channels: {self.channels}")
            print()
        
        try:
            if AUDIO_BACKEND == "sounddevice":
                return self._record_sounddevice(filepath, duration, show_progress)
            elif AUDIO_BACKEND == "pyaudio":
                return self._record_pyaudio(filepath, duration, show_progress)
            else:
                raise MicrophoneError("No audio backend available")
                
        except Exception as e:
            return RecordingResult(
                filepath=str(filepath),
                duration_sec=0,
                sample_rate=self.sample_rate,
                channels=self.channels,
                file_size_bytes=0,
                success=False,
                error=str(e)
            )
    
    def _record_sounddevice(
        self,
        filepath: Path,
        duration: float,
        show_progress: bool
    ) -> RecordingResult:
        """Record using sounddevice backend."""
        frames = int(duration * self.sample_rate)
        
        if show_progress:
            print("  🎙️  Recording... ", end="", flush=True)
        
        # Record audio
        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            device=self.device_id
        )
        
        # Show countdown
        if show_progress:
            for i in range(int(duration), 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
        
        sd.wait()  # Wait for recording to complete
        
        if show_progress:
            print("Done!")
        
        # Save to WAV file
        sf.write(str(filepath), recording, self.sample_rate)
        
        # Get file info
        file_size = filepath.stat().st_size
        
        if show_progress:
            print(f"\n  ✓ Saved: {filepath}")
            print(f"  ✓ Size: {file_size / 1024:.1f} KB")
        
        return RecordingResult(
            filepath=str(filepath),
            duration_sec=duration,
            sample_rate=self.sample_rate,
            channels=self.channels,
            file_size_bytes=file_size,
            success=True
        )
    
    def _record_pyaudio(
        self,
        filepath: Path,
        duration: float,
        show_progress: bool
    ) -> RecordingResult:
        """Record using PyAudio backend."""
        chunk = 1024
        format = pyaudio.paInt16
        
        p = pyaudio.PyAudio()
        
        if show_progress:
            print("  🎙️  Recording... ", end="", flush=True)
        
        stream = p.open(
            format=format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_id,
            frames_per_buffer=chunk
        )
        
        frames = []
        total_chunks = int(self.sample_rate / chunk * duration)
        
        for i in range(total_chunks):
            data = stream.read(chunk)
            frames.append(data)
            
            # Show progress
            if show_progress and i % (self.sample_rate // chunk) == 0:
                remaining = int(duration - (i * chunk / self.sample_rate))
                print(f"{remaining}...", end=" ", flush=True)
        
        if show_progress:
            print("Done!")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to WAV file
        wf = wave.open(str(filepath), 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Get file info
        file_size = filepath.stat().st_size
        
        if show_progress:
            print(f"\n  ✓ Saved: {filepath}")
            print(f"  ✓ Size: {file_size / 1024:.1f} KB")
        
        return RecordingResult(
            filepath=str(filepath),
            duration_sec=duration,
            sample_rate=self.sample_rate,
            channels=self.channels,
            file_size_bytes=file_size,
            success=True
        )
    
    def record_until_silence(
        self,
        max_duration: float = 30.0,
        silence_threshold: float = 0.01,
        silence_duration: float = 2.0,
        filename: Optional[str] = None
    ) -> RecordingResult:
        """
        Record until silence is detected.
        
        Args:
            max_duration: Maximum recording time
            silence_threshold: Volume threshold for silence
            silence_duration: How long silence before stopping
            filename: Custom filename
            
        Returns:
            RecordingResult object
        """
        # For now, fall back to fixed duration
        # Full implementation requires streaming detection
        print("[INFO] Recording for max duration (silence detection coming soon)")
        return self.record(duration=max_duration, filename=filename)
    
    def get_info(self) -> dict:
        """Get recorder configuration."""
        return {
            "backend": AUDIO_BACKEND,
            "output_dir": str(self.output_dir),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "device_id": self.device_id,
            "mic_info": self.mic.get_info()
        }


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface for audio recording."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Audio Recorder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python recorder.py record --duration 5
  python recorder.py record --duration 10 --output my_audio.wav
  python recorder.py devices
  python recorder.py test
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Record command
    rec_parser = subparsers.add_parser("record", help="Record audio")
    rec_parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duration in seconds (default: 5)")
    rec_parser.add_argument("--output", "-o", help="Output filename")
    rec_parser.add_argument("--device", type=int, help="Input device ID")
    
    # Devices command
    dev_parser = subparsers.add_parser("devices", help="List input devices")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test microphone")
    test_parser.add_argument("--device", type=int, help="Device ID to test")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show recorder info")
    
    args = parser.parse_args()
    
    if args.command == "record":
        recorder = AudioRecorder(device_id=args.device if hasattr(args, 'device') else None)
        result = recorder.record(
            duration=args.duration,
            filename=args.output
        )
        
        if result.success:
            print(f"\n[SUCCESS] Recording saved!")
            print(f"  File: {result.filepath}")
            print(f"  Duration: {result.duration_sec}s")
            print(f"  Size: {result.file_size_bytes / 1024:.1f} KB")
        else:
            print(f"\n[ERROR] Recording failed: {result.error}")
            sys.exit(1)
    
    elif args.command == "devices":
        from .mic import print_devices
        print_devices()
    
    elif args.command == "test":
        mic = Microphone(device_id=args.device if hasattr(args, 'device') else None)
        print("\n[TESTING] Microphone...")
        print(f"  Device: {mic.get_default_device()['name'] if mic.get_default_device() else 'Unknown'}")
        
        if mic.test_device(2.0):
            print("\n  ✓ Microphone is working!")
        else:
            print("\n  ✗ Microphone test failed!")
            sys.exit(1)
    
    elif args.command == "info":
        recorder = AudioRecorder()
        info = recorder.get_info()
        
        print("\n" + "=" * 50)
        print("RECORDER INFO")
        print("=" * 50)
        for k, v in info.items():
            if k != "mic_info":
                print(f"  {k}: {v}")
        print("=" * 50)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()