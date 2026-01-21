"""
Speechee - Live Speech-to-Text
Real-time voice recording and transcription pipeline.
"""

import sys
import time
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from audio.recorder import AudioRecorder
from audio.mic import Microphone


try:
    from .offline import OfflineTranscriber
    from .exceptions import SpeecheeError
except ImportError:
    from offline import OfflineTranscriber
    from exceptions import SpeecheeError

# Optional: Colors for CLI
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


@dataclass
class LiveSTTResult:
    """Result of live STT operation."""
    text: str
    duration_sec: float
    recording_time_sec: float
    transcription_time_sec: float
    total_latency_sec: float
    model: str
    audio_file: str
    success: bool
    error: Optional[str] = None
    
    def print_summary(self, verbose: bool = False):
        """Print formatted result."""
        print("\n" + "=" * 60)
        if self.success:
            print(f"{Fore.GREEN}✓ TRANSCRIPTION SUCCESS{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ TRANSCRIPTION FAILED{Style.RESET_ALL}")
        print("=" * 60)
        
        if self.success:
            print(f"\n{Fore.CYAN}Text:{Style.RESET_ALL}")
            print(f'  "{self.text}"')
            
            print(f"\n{Fore.YELLOW}Performance:{Style.RESET_ALL}")
            print(f"  Recording:      {self.recording_time_sec:.2f}s")
            print(f"  Transcription:  {self.transcription_time_sec:.2f}s")
            print(f"  Total Latency:  {self.total_latency_sec:.2f}s")
            
            if verbose:
                print(f"\n{Fore.YELLOW}Details:{Style.RESET_ALL}")
                print(f"  Model:        {self.model}")
                print(f"  Audio File:   {self.audio_file}")
        else:
            print(f"\n{Fore.RED}Error:{Style.RESET_ALL} {self.error}")
        
        print("=" * 60)


class LiveSTT:
    """
    Live Speech-to-Text system.
    
    Usage:
        live_stt = LiveSTT(model="tiny.en")
        result = live_stt.listen(duration=5)
        print(result.text)
    """
    
    def __init__(
        self,
        model: str = "tiny.en",
        language: str = "auto",
        device_id: Optional[int] = None,
        cleanup: bool = True,
        verbose: bool = False
    ):
        """
        Initialize live STT system.
        
        Args:
            model: Whisper model name
            language: Language code or "auto"
            device_id: Microphone device ID
            cleanup: Auto-delete temp files
            verbose: Print debug info
        """
        self.model = model
        self.language = language
        self.device_id = device_id
        self.cleanup = cleanup
        self.verbose = verbose
        
        # Initialize components
        if self.verbose:
            print(f"\n{Fore.CYAN}[INIT] Initializing Live STT...{Style.RESET_ALL}")
        
        try:
            self.recorder = AudioRecorder(device_id=device_id)
            if self.verbose:
                print(f"  ✓ Recorder ready")
            
            self.transcriber = OfflineTranscriber(
                model=model,
                language=language,
                verbose=verbose
            )
            if self.verbose:
                print(f"  ✓ Transcriber ready (model: {model})")
                print(f"  ✓ Live STT initialized")
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Initialization failed: {e}{Style.RESET_ALL}")
            raise
    
    def listen(
        self,
        duration: float = 5.0,
        filename: Optional[str] = None,
        keep_audio: bool = False
    ) -> LiveSTTResult:
        """
        Record audio and transcribe.
        
        Args:
            duration: Recording duration in seconds
            filename: Custom filename for recording
            keep_audio: Keep audio file after transcription
            
        Returns:
            LiveSTTResult object
        """
        audio_file = None
        start_time = time.time()
        
        try:
            # Step 1: Record audio
            if self.verbose:
                print(f"\n{Fore.CYAN}[STEP 1/3] Recording audio...{Style.RESET_ALL}")
            
            record_start = time.time()
            recording_result = self.recorder.record(
                duration=duration,
                filename=filename,
                show_progress=True
            )
            record_time = time.time() - record_start
            
            if not recording_result.success:
                return LiveSTTResult(
                    text="",
                    duration_sec=duration,
                    recording_time_sec=record_time,
                    transcription_time_sec=0,
                    total_latency_sec=time.time() - start_time,
                    model=self.model,
                    audio_file="",
                    success=False,
                    error=recording_result.error
                )
            
            audio_file = recording_result.filepath
            
            # Step 2: Transcribe
            if self.verbose:
                print(f"\n{Fore.CYAN}[STEP 2/3] Transcribing...{Style.RESET_ALL}")
            
            transcribe_start = time.time()
            transcription_result = self.transcriber.transcribe(
                audio_file,
                output_format="txt"
            )
            transcribe_time = time.time() - transcribe_start
            
            total_time = time.time() - start_time
            
            # Step 3: Cleanup
            if self.cleanup and not keep_audio:
                if self.verbose:
                    print(f"\n{Fore.CYAN}[STEP 3/3] Cleaning up...{Style.RESET_ALL}")
                try:
                    Path(audio_file).unlink()
                    if self.verbose:
                        print(f"  ✓ Deleted temp file: {Path(audio_file).name}")
                except Exception as e:
                    if self.verbose:
                        print(f"  ⚠ Cleanup failed: {e}")
            
            return LiveSTTResult(
                text=transcription_result.text,
                duration_sec=duration,
                recording_time_sec=record_time,
                transcription_time_sec=transcribe_time,
                total_latency_sec=total_time,
                model=self.model,
                audio_file=audio_file,
                success=transcription_result.success,
                error=transcription_result.error
            )
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[CANCELLED] Interrupted by user{Style.RESET_ALL}")
            if audio_file and self.cleanup and Path(audio_file).exists():
                Path(audio_file).unlink()
            raise
            
        except Exception as e:
            error_msg = str(e)
            if self.verbose:
                print(f"\n{Fore.RED}[ERROR] {error_msg}{Style.RESET_ALL}")
            
            # Cleanup on error
            if audio_file and self.cleanup and Path(audio_file).exists():
                try:
                    Path(audio_file).unlink()
                except Exception:
                    pass
            
            return LiveSTTResult(
                text="",
                duration_sec=duration,
                recording_time_sec=0,
                transcription_time_sec=0,
                total_latency_sec=time.time() - start_time,
                model=self.model,
                audio_file=audio_file or "",
                success=False,
                error=error_msg
            )
    
    def listen_continuous(
        self,
        duration_per_chunk: float = 5.0,
        max_chunks: int = 10,
        pause_between: float = 1.0
    ):
        """
        Continuous listening mode (multiple recordings).
        
        Args:
            duration_per_chunk: Duration of each recording
            max_chunks: Maximum number of recordings
            pause_between: Pause between recordings
        """
        print(f"\n{Fore.CYAN}Starting continuous listening mode...{Style.RESET_ALL}")
        print(f"  Duration per chunk: {duration_per_chunk}s")
        print(f"  Max chunks: {max_chunks}")
        print(f"  Press Ctrl+C to stop")
        
        chunk_num = 0
        
        try:
            while chunk_num < max_chunks:
                chunk_num += 1
                print(f"\n{Fore.YELLOW}[Chunk {chunk_num}/{max_chunks}]{Style.RESET_ALL}")
                
                result = self.listen(duration=duration_per_chunk)
                result.print_summary(verbose=False)
                
                if chunk_num < max_chunks:
                    print(f"\n{Fore.CYAN}Waiting {pause_between}s...{Style.RESET_ALL}")
                    time.sleep(pause_between)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Continuous mode stopped.{Style.RESET_ALL}")
    
    def get_info(self) -> dict:
        """Get system configuration."""
        return {
            "model": self.model,
            "language": self.language,
            "device_id": self.device_id,
            "cleanup": self.cleanup,
            "recorder_info": self.recorder.get_info(),
            "transcriber_info": self.transcriber.get_info()
        }


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Live Speech-to-Text System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Listen for 5 seconds (default)
  python live_stt.py listen
  
  # Listen for 10 seconds
  python live_stt.py listen --duration 10
  
  # Use different model
  python live_stt.py listen --model base --language hi
  
  # Keep audio file
  python live_stt.py listen --keep-audio
  
  # Continuous mode
  python live_stt.py continuous --duration 5 --chunks 3
  
  # Show system info
  python live_stt.py info

Audio Recording:
  python audio\\recorder.py record --duration 5
  python audio\\recorder.py devices
  python audio\\recorder.py test

Audio Processing:
  python audio\\preprocess.py info audio.wav
  python audio\\preprocess.py check audio.wav
  python audio\\preprocess.py convert audio.mp3

Transcription:
  python stt\\offline.py transcribe audio.wav
  python stt\\offline.py info
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Listen command
    listen_parser = subparsers.add_parser("listen", help="Record and transcribe once")
    listen_parser.add_argument(
        "--duration", "-d",
        type=float,
        default=5.0,
        help="Recording duration in seconds (default: 5)"
    )
    listen_parser.add_argument(
        "--model", "-m",
        default="tiny.en",
        help="Whisper model (default: tiny.en)"
    )
    listen_parser.add_argument(
        "--language", "-l",
        default="auto",
        help="Language code or auto (default: auto)"
    )
    listen_parser.add_argument(
        "--device",
        type=int,
        help="Microphone device ID"
    )
    listen_parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep audio file after transcription"
    )
    listen_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't delete temp files"
    )
    listen_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    # Continuous command
    cont_parser = subparsers.add_parser("continuous", help="Continuous listening mode")
    cont_parser.add_argument(
        "--duration", "-d",
        type=float,
        default=5.0,
        help="Duration per chunk (default: 5)"
    )
    cont_parser.add_argument(
        "--chunks", "-c",
        type=int,
        default=10,
        help="Maximum chunks (default: 10)"
    )
    cont_parser.add_argument(
        "--pause", "-p",
        type=float,
        default=1.0,
        help="Pause between chunks (default: 1s)"
    )
    cont_parser.add_argument(
        "--model", "-m",
        default="tiny.en",
        help="Whisper model"
    )
    cont_parser.add_argument(
        "--language", "-l",
        default="auto",
        help="Language code"
    )
    cont_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show system info")
    info_parser.add_argument("--model", "-m", default="tiny.en", help="Model to check")
    
    # Devices command
    dev_parser = subparsers.add_parser("devices", help="List audio devices")
    
    args = parser.parse_args()
    
    if args.command == "listen":
        try:
            live_stt = LiveSTT(
                model=args.model,
                language=args.language,
                device_id=args.device if hasattr(args, 'device') and args.device else None,
                cleanup=not args.no_cleanup,
                verbose=args.verbose
            )
            
            result = live_stt.listen(
                duration=args.duration,
                keep_audio=args.keep_audio
            )
            
            result.print_summary(verbose=args.verbose)
            
            sys.exit(0 if result.success else 1)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    elif args.command == "continuous":
        try:
            live_stt = LiveSTT(
                model=args.model,
                language=args.language,
                verbose=args.verbose
            )
            
            live_stt.listen_continuous(
                duration_per_chunk=args.duration,
                max_chunks=args.chunks,
                pause_between=args.pause
            )
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopped.{Style.RESET_ALL}")
    
    elif args.command == "info":
        try:
            live_stt = LiveSTT(model=args.model)
            info = live_stt.get_info()
            
            print("\n" + "=" * 60)
            print("LIVE STT SYSTEM INFO")
            print("=" * 60)
            
            print(f"\n{Fore.CYAN}Configuration:{Style.RESET_ALL}")
            print(f"  Model:    {info['model']}")
            print(f"  Language: {info['language']}")
            print(f"  Device:   {info['device_id'] or 'Default'}")
            print(f"  Cleanup:  {info['cleanup']}")
            
            print(f"\n{Fore.CYAN}Components:{Style.RESET_ALL}")
            rec_info = info['recorder_info']
            print(f"  Audio Backend:    {rec_info.get('backend', 'N/A')}")
            print(f"  Sample Rate:      {rec_info.get('sample_rate', 'N/A')} Hz")
            print(f"  Channels:         {rec_info.get('channels', 'N/A')}")
            
            trans_info = info['transcriber_info']
            print(f"  Binary Exists:    {trans_info.get('binary_exists', False)}")
            print(f"  Model Exists:     {trans_info.get('model_exists', False)}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    elif args.command == "devices":
        from audio.mic import print_devices
        print_devices()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()