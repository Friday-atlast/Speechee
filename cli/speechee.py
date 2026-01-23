#!/usr/bin/env python3
"""
Speechee CLI — Unified Command Line Interface
Offline-first Speech-to-Text system.

Usage:
    speechee listen              # Live mic transcription
    speechee transcribe FILE     # File transcription
    speechee record              # Record audio
    speechee models list         # List models
    speechee config show         # Show configuration
    speechee --help              # Show help
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Optional: Colors for CLI
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""


# ================================================================
# BANNER & HELPERS
# ================================================================

VERSION = "1.0.0-dev"

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Fore.WHITE}███████╗██████╗ ███████╗███████╗ ██████╗██╗  ██╗███████╗███████╗{Fore.CYAN}   ║
║   {Fore.WHITE}██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝██║  ██║██╔════╝██╔════╝{Fore.CYAN}   ║
║   {Fore.WHITE}███████╗██████╔╝█████╗  █████╗  ██║     ███████║█████╗  █████╗{Fore.CYAN}     ║
║   {Fore.WHITE}╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║     ██╔══██║██╔══╝  ██╔══╝{Fore.CYAN}     ║
║   {Fore.WHITE}███████║██║     ███████╗███████╗╚██████╗██║  ██║███████╗███████╗{Fore.CYAN}   ║
║   {Fore.WHITE}╚══════╝╚═╝     ╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝{Fore.CYAN}   ║
║                                                                      ║
║   {Fore.YELLOW}Offline-First Speech-to-Text{Fore.CYAN}                                       ║
║   {Fore.WHITE}Version: {VERSION}{Fore.CYAN}                                                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

def print_banner():
    """Print Speechee banner."""
    print(BANNER)


def print_success(message: str):
    """Print success message."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


# ================================================================
# COMMAND HANDLERS
# ================================================================

def cmd_listen(args):
    """Handle 'listen' command — Live mic transcription."""
    try:
        from stt import LiveSTT, OutputManager
        from config import get_settings
        
        settings = get_settings()
        
        # Get defaults from config
        model = args.model if args.model else settings.get("stt.model", "tiny.en")
        language = args.language if args.language else settings.get("stt.language", "auto")
        duration = args.duration if args.duration is not None else settings.get("audio.default_duration", 5)
        
        print_info(f"Initializing Live STT (model: {model})...")
        
        live = LiveSTT(
            model=model,
            language=language,
            cleanup=not args.keep_audio,
            verbose=args.verbose
        )
        
        print_info(f"Recording for {duration} seconds...")
        print(f"{Fore.YELLOW}🎙️  Speak now...{Style.RESET_ALL}\n")
        
        result = live.listen(
            duration=duration,
            keep_audio=args.keep_audio
        )
        
        if result.success:
            print("\n" + "=" * 60)
            print(f"{Fore.GREEN}✓ TRANSCRIPTION SUCCESS{Style.RESET_ALL}")
            print("=" * 60)
            print(f"\n{Fore.CYAN}Text:{Style.RESET_ALL}")
            print(f'  "{result.text}"')
            print(f"\n{Fore.YELLOW}Performance:{Style.RESET_ALL}")
            print(f"  Latency: {result.total_latency_sec:.2f}s")
            print("=" * 60)
            
            # Auto-save if configured or requested
            if args.save or settings.get("output.auto_save", False):
                manager = OutputManager()
                output_format = args.format or settings.get("output.format", "txt")
                saved = manager.save_from_result(result, format=output_format)
                print_success(f"Saved to: {saved.filepath}")
            
            return 0
        else:
            print_error(f"Transcription failed: {result.error}")
            return 1
            
    except KeyboardInterrupt:
        print_warning("\nCancelled by user.")
        return 1
    except Exception as e:
        print_error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_transcribe(args):
    """Handle 'transcribe' command — File transcription."""
    try:
        from stt import OfflineTranscriber, OutputManager
        from config import get_settings
        
        settings = get_settings()
        
        # Get defaults from config
        model = args.model or settings.get("stt.model", "tiny.en")
        language = args.language or settings.get("stt.language", "auto")
        
        # Validate file
        audio_path = Path(args.file)
        if not audio_path.exists():
            print_error(f"File not found: {args.file}")
            return 1
        
        print_info(f"Transcribing: {audio_path.name}")
        print_info(f"Model: {model}")
        
        transcriber = OfflineTranscriber(
            model=model,
            language=language,
            verbose=args.verbose
        )
        
        result = transcriber.transcribe(
            str(audio_path),
            output_format=args.format or settings.get("output.format", "txt")
        )
        
        if result.success:
            print("\n" + "=" * 60)
            print(f"{Fore.GREEN}✓ TRANSCRIPTION SUCCESS{Style.RESET_ALL}")
            print("=" * 60)
            print(f"\n{Fore.CYAN}Text:{Style.RESET_ALL}")
            print(f'  "{result.text}"')
            print("=" * 60)
            
            # Save if requested
            if args.save or settings.get("output.auto_save", False):
                manager = OutputManager()
                saved = manager.save_from_result(result, format=args.format or "txt")
                print_success(f"Saved to: {saved.filepath}")
            
            # Output to file
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result.text)
                print_success(f"Written to: {args.output}")
            
            return 0
        else:
            print_error(f"Transcription failed: {result.error}")
            return 1
            
    except Exception as e:
        print_error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_record(args):
    """Handle 'record' command — Audio recording."""
    try:
        from audio import AudioRecorder
        from config import get_settings
        
        settings = get_settings()
        duration = args.duration if args.duration is not None else settings.get("audio.default_duration", 5)
        
        print_info(f"Recording for {duration} seconds...")
        print(f"{Fore.YELLOW}🎙️  Recording...{Style.RESET_ALL}\n")
        
        recorder = AudioRecorder()
        result = recorder.record(
            duration=duration,
            filename=args.output,
            show_progress=True
        )
        
        if result.success:
            print_success(f"Saved: {result.filepath}")
            print_info(f"Size: {result.file_size_bytes / 1024:.1f} KB")
            return 0
        else:
            print_error(f"Recording failed: {result.error}")
            return 1
            
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def cmd_models(args):
    """Handle 'models' command — Model management."""
    try:
        from engine import ModelManager, EngineConfig
        
        manager = ModelManager()
        
        if args.models_cmd == "list":
            manager.list_models()
        
        elif args.models_cmd == "download":
            if not args.name:
                print_error("Model name required. Use: speechee models download <name>")
                print_info(f"Available: {EngineConfig.list_all_models()}")
                return 1
            manager.download_model(args.name, force=args.force)
        
        elif args.models_cmd == "verify":
            if not args.name:
                # Verify all
                for model in EngineConfig.list_all_models():
                    result = manager.verify_model(model)
                    status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if result.get("valid") else f"{Fore.RED}✗{Style.RESET_ALL}"
                    print(f"  {model}: {status}")
            else:
                result = manager.verify_model(args.name)
                if result.get("valid"):
                    print_success(f"{args.name} is valid")
                else:
                    print_error(f"{args.name}: {result.get('error', 'Invalid')}")
        
        elif args.models_cmd == "recommended":
            manager.download_recommended(force=args.force)
            manager.list_models()
        
        elif args.models_cmd == "all":
            manager.download_all(force=args.force)
            manager.list_models()
        
        else:
            manager.list_models()
        
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def cmd_devices(args):
    """Handle 'devices' command — List audio devices."""
    try:
        from audio import Microphone
        
        mic = Microphone()
        devices = mic.list_devices()
        
        print("\n" + "=" * 60)
        print("AUDIO INPUT DEVICES")
        print("=" * 60)
        
        if not devices:
            print_warning("No input devices found.")
        else:
            print(f"\n{'ID':<5} {'Name':<45} {'Default':<8}")
            print("-" * 60)
            for dev in devices:
                default = f"{Fore.GREEN}✓{Style.RESET_ALL}" if dev.get('is_default') else ""
                name = dev['name'][:43] if len(dev['name']) > 43 else dev['name']
                print(f"{dev['index']:<5} {name:<45} {default:<8}")
        
        print("=" * 60)
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def cmd_info(args):
    """Handle 'info' command — System information."""
    try:
        from engine import EngineConfig
        from config import get_settings
        
        settings = get_settings()
        
        print("\n" + "=" * 60)
        print("SPEECHEE SYSTEM INFO")
        print("=" * 60)
        
        print(f"\n{Fore.CYAN}Version:{Style.RESET_ALL} {VERSION}")
        print(f"{Fore.CYAN}Project:{Style.RESET_ALL} {PROJECT_ROOT}")
        
        # Config info
        print(f"\n{Fore.YELLOW}Config:{Style.RESET_ALL}")
        print(f"  Model: {settings.get('stt.model')}")
        print(f"  Language: {settings.get('stt.language')}")
        print(f"  Duration: {settings.get('audio.default_duration')}s")
        
        # Engine status
        print(f"\n{Fore.YELLOW}Engine:{Style.RESET_ALL}")
        binary_exists = EngineConfig.WHISPER_BINARY.exists()
        status = f"{Fore.GREEN}✓ Ready{Style.RESET_ALL}" if binary_exists else f"{Fore.RED}✗ Not Built{Style.RESET_ALL}"
        print(f"  whisper-cli: {status}")
        
        # Check models
        print(f"\n{Fore.YELLOW}Models:{Style.RESET_ALL}")
        downloaded = EngineConfig.list_downloaded_models()
        total = len(EngineConfig.list_all_models())
        print(f"  Downloaded: {len(downloaded)}/{total}")
        for model in downloaded:
            print(f"    ✓ {model}")
        
        # Check audio
        print(f"\n{Fore.YELLOW}Audio:{Style.RESET_ALL}")
        try:
            from audio import Microphone
            mic = Microphone()
            devices = mic.list_devices()
            print(f"  Input devices: {len(devices)}")
            default = mic.get_default_device()
            if default:
                print(f"  Default: {default['name'][:40]}")
        except Exception as e:
            print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}")
        
        print("\n" + "=" * 60)
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def cmd_outputs(args):
    """Handle 'outputs' command — Manage saved transcripts."""
    try:
        from stt import OutputManager
        
        manager = OutputManager()
        
        if args.outputs_cmd == "list":
            transcripts = manager.list_transcripts(limit=args.limit)
            
            print("\n" + "=" * 70)
            print("SAVED TRANSCRIPTS")
            print("=" * 70)
            
            if not transcripts:
                print_info("No transcripts found.")
            else:
                print(f"\n{'Filename':<40} {'Format':<8} {'Size':<12}")
                print("-" * 70)
                for t in transcripts:
                    size = f"{t.size_bytes/1024:.1f} KB" if t.size_bytes > 1024 else f"{t.size_bytes} B"
                    print(f"{t.filename:<40} {t.format:<8} {size:<12}")
            
            print("=" * 70)
        
        elif args.outputs_cmd == "stats":
            stats = manager.get_stats()
            
            print("\n" + "=" * 50)
            print("TRANSCRIPT STATISTICS")
            print("=" * 50)
            print(f"\n  Total Files: {stats['total_files']}")
            print(f"  Total Size:  {stats['total_size_kb']} KB")
            print(f"  Directory:   {stats['output_dir']}")
            print("=" * 50)
        
        elif args.outputs_cmd == "clear":
            if not args.confirm:
                print_warning("Use --confirm to delete all transcripts")
                return 1
            count = manager.clear_all(confirm=True)
            print_success(f"Deleted {count} files")
        
        else:
            # Default to list
            transcripts = manager.list_transcripts(limit=10)
            if transcripts:
                print(f"\n{Fore.CYAN}Recent Transcripts:{Style.RESET_ALL}")
                for t in transcripts[:5]:
                    print(f"  - {t.filename}")
            else:
                print_info("No transcripts saved yet.")
        
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def cmd_config(args):
    """Handle 'config' command — Configuration management."""
    try:
        from config import Settings
        from config.settings import CONFIG_DIR, USER_CONFIG_FILE, DEFAULTS_FILE
        
        settings = Settings()
        
        if args.config_cmd == "show":
            if args.config_args:
                settings.print_config(args.config_args[0])
            else:
                settings.print_config()
        
        elif args.config_cmd == "get":
            if not args.config_args:
                print_error("Key required. Example: speechee config get stt.model")
                return 1
            key = args.config_args[0]
            value = settings.get(key)
            if value is not None:
                print(f"{Fore.CYAN}{key}{Style.RESET_ALL} = {value}")
            else:
                print_warning(f"Key not found: {key}")
        
        elif args.config_cmd == "set":
            if len(args.config_args) < 2:
                print_error("Key and value required. Example: speechee config set stt.model base")
                return 1
            key = args.config_args[0]
            value = args.config_args[1]
            
            # Parse value type
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.lower() in ("null", "none"):
                value = None
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            
            settings.set(key, value, persist=True)
            print_success(f"Set {key} = {value}")
        
        elif args.config_cmd == "reset":
            if args.config_args:
                key = args.config_args[0]
                settings.reset(key)
                settings.save()
                print_success(f"Reset: {key}")
            else:
                print_warning("Use 'speechee config reset <key>' to reset specific key")
        
        elif args.config_cmd == "validate":
            result = settings.validate()
            if result["valid"]:
                print_success("Configuration is valid")
            else:
                print_warning("Configuration issues:")
                for issue in result["issues"]:
                    print(f"  - {issue}")
        
        elif args.config_cmd == "path":
            print(f"\n{Fore.CYAN}Config Directory:{Style.RESET_ALL} {CONFIG_DIR}")
            print(f"{Fore.CYAN}User Config:{Style.RESET_ALL}      {USER_CONFIG_FILE}")
            print(f"{Fore.CYAN}Defaults:{Style.RESET_ALL}         {DEFAULTS_FILE}")
        
        else:
            settings.print_config()
        
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1

def cmd_language(args):
    """Handle 'language' command — Language detection and info."""
    try:
        from stt import LanguageManager
        
        lm = LanguageManager()
        
        if args.lang_cmd == "detect":
            if not args.text:
                print_error("Text required. Example: speechee language detect 'Hello world'")
                return 1
            
            text = " ".join(args.text)
            result = lm.detect(text)
            is_hinglish, mix_ratio = lm.detect_hinglish(text)
            
            print("\n" + "=" * 50)
            print("LANGUAGE DETECTION")
            print("=" * 50)
            print(f"\n  Text: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
            print(f"\n  {Fore.CYAN}Detected:{Style.RESET_ALL} {result.name} ({result.code})")
            print(f"  {Fore.CYAN}Confidence:{Style.RESET_ALL} {result.confidence:.1%}")
            print(f"  {Fore.CYAN}Method:{Style.RESET_ALL} {result.method}")
            
            if is_hinglish:
                print(f"\n  {Fore.YELLOW}⚠ Hinglish detected (mix: {mix_ratio:.1%}){Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Tip:{Style.RESET_ALL} Use multilingual model (tiny, base)")
            
            print("=" * 50)
        
        elif args.lang_cmd == "list":
            lm.print_languages()
        
        elif args.lang_cmd == "model":
            if not args.text:
                print_error("Language code required. Example: speechee language model hi")
                return 1
            
            lang_code = args.text[0]
            quality = args.quality or "balanced"
            
            model = lm.get_recommended_model(lang_code, quality)
            requires_multi = lm.requires_multilingual_model(lang_code)
            
            print(f"\n  Language: {lm.get_language_name(lang_code)} ({lang_code})")
            print(f"  Quality: {quality}")
            print(f"  Recommended Model: {Fore.GREEN}{model}{Style.RESET_ALL}")
            print(f"  Requires Multilingual: {requires_multi}")
        
        else:
            lm.print_languages()
        
        return 0
        
    except Exception as e:
        print_error(f"Error: {e}")
        return 1

# ================================================================
# MAIN CLI
# ================================================================

def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="speechee",
        description="Speechee — Offline-First Speech-to-Text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.CYAN}Commands:{Style.RESET_ALL}
  listen      Record from microphone and transcribe
  transcribe  Transcribe audio file
  record      Record audio to file
  models      Manage whisper models
  devices     List audio input devices
  outputs     Manage saved transcripts
  config      View and modify configuration
  info        Show system information

{Fore.CYAN}Examples:{Style.RESET_ALL}
  speechee listen                         # Record 5s and transcribe
  speechee listen -d 10                   # Record 10 seconds
  speechee listen -m base                 # Use base model
  speechee listen --save                  # Save transcript
  
  speechee transcribe audio.wav           # Transcribe file
  speechee transcribe audio.wav -m base   # Use base model
  speechee transcribe audio.wav --save    # Save transcript
  
  speechee record -d 5                    # Record 5 seconds
  speechee record -d 10 -o my_audio.wav   # Custom filename

  speechee config show                    # Show all config
  speechee config get stt.model           # Get specific value
  speechee config set stt.model base      # Set value
  
  speechee models list                    # List models
  speechee models download base           # Download base model
  speechee models recommended             # Download recommended
  
  speechee devices                        # List audio devices
  speechee outputs list                   # List saved transcripts
  speechee info                           # System info

{Fore.CYAN}Documentation:{Style.RESET_ALL}
  See docs/ folder for detailed guides.
        """
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Speechee {VERSION}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # ---- listen command ----
    listen_parser = subparsers.add_parser(
        "listen",
        help="Record from microphone and transcribe",
        description="Record audio from microphone and transcribe to text."
    )
    listen_parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Recording duration in seconds"
    )
    listen_parser.add_argument(
        "-m", "--model",
        help="Whisper model"
    )
    listen_parser.add_argument(
        "-l", "--language",
        help="Language code or 'auto'"
    )
    listen_parser.add_argument(
        "--save",
        action="store_true",
        help="Save transcript to file"
    )
    listen_parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "srt", "vtt"],
        help="Output format"
    )
    listen_parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep audio file after transcription"
    )
    listen_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    # ---- transcribe command ----
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio file",
        description="Transcribe audio file to text."
    )
    transcribe_parser.add_argument(
        "file",
        help="Path to audio file"
    )
    transcribe_parser.add_argument(
        "-m", "--model",
        help="Whisper model"
    )
    transcribe_parser.add_argument(
        "-l", "--language",
        help="Language code or 'auto'"
    )
    transcribe_parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    transcribe_parser.add_argument(
        "--save",
        action="store_true",
        help="Save transcript to output/transcripts/"
    )
    transcribe_parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "srt", "vtt"],
        help="Output format"
    )
    transcribe_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    # ---- record command ----
    record_parser = subparsers.add_parser(
        "record",
        help="Record audio to file",
        description="Record audio from microphone and save to file."
    )
    record_parser.add_argument(
        "-d", "--duration",
        type=float,
        help="Recording duration in seconds"
    )
    record_parser.add_argument(
        "-o", "--output",
        help="Output filename"
    )
    
    # ---- models command ----
    models_parser = subparsers.add_parser(
        "models",
        help="Manage whisper models",
        description="Download and manage whisper models."
    )
    models_parser.add_argument(
        "models_cmd",
        nargs="?",
        choices=["list", "download", "verify", "recommended", "all"],
        default="list",
        help="Models subcommand"
    )
    models_parser.add_argument(
        "name",
        nargs="?",
        help="Model name for download/verify"
    )
    models_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download"
    )
    
    # ---- devices command ----
    devices_parser = subparsers.add_parser(
        "devices",
        help="List audio input devices",
        description="List available audio input devices."
    )
    
    # ---- outputs command ----
    outputs_parser = subparsers.add_parser(
        "outputs",
        help="Manage saved transcripts",
        description="List and manage saved transcript files."
    )
    outputs_parser.add_argument(
        "outputs_cmd",
        nargs="?",
        choices=["list", "stats", "clear"],
        default="list",
        help="Outputs subcommand"
    )
    outputs_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of files shown"
    )
    outputs_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive operations"
    )
    
    # ---- info command ----
    info_parser = subparsers.add_parser(
        "info",
        help="Show system information",
        description="Show Speechee system information and status."
    )

    # ---- config command ----
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration",
        description="View and modify Speechee configuration."
    )
    config_parser.add_argument(
        "config_cmd",
        nargs="?",
        choices=["show", "get", "set", "reset", "validate", "path"],
        default="show",
        help="Config subcommand"
    )
    config_parser.add_argument(
        "config_args",
        nargs="*",
        help="Additional arguments (key, value)"
    )
    
    # ---- language command ----
    lang_parser = subparsers.add_parser(
        "language",
        help="Language detection and info",
        description="Detect language and get model recommendations."
    )
    lang_parser.add_argument(
        "lang_cmd",
        nargs="?",
        choices=["detect", "list", "model"],
        default="list",
        help="Language subcommand"
    )
    lang_parser.add_argument(
        "text",
        nargs="*",
        help="Text to analyze or language code"
    )
    lang_parser.add_argument(
        "--quality", "-q",
        choices=["fast", "balanced", "accurate"],
        help="Model quality preference"
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # No command given
    if not args.command:
        print_banner()
        parser.print_help()
        return 0
    
    # Route to command handler
    commands = {
        "listen": cmd_listen,
        "transcribe": cmd_transcribe,
        "record": cmd_record,
        "models": cmd_models,
        "devices": cmd_devices,
        "outputs": cmd_outputs,
        "config": cmd_config,
        "info": cmd_info,
        "language": cmd_language,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())