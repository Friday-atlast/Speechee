"""
Speechee - Output Manager
Save and load transcription outputs.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .formatter import OutputFormatter, TranscriptSegment
except ImportError:
    from formatter import OutputFormatter, TranscriptSegment


@dataclass
class SavedTranscript:
    """Information about a saved transcript."""
    filepath: str
    filename: str
    format: str
    size_bytes: int
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "filepath": self.filepath,
            "filename": self.filename,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at
        }


class OutputManager:
    """
    Manage transcription output files.
    
    Handles:
    - Saving transcripts in multiple formats
    - Loading saved transcripts
    - Listing saved files
    - Auto-naming with timestamps
    
    Usage:
        manager = OutputManager()
        
        # Save transcript
        path = manager.save("Hello world", format="json")
        
        # Save with custom name
        path = manager.save("Hello world", filename="my_transcript", format="txt")
        
        # List saved transcripts
        files = manager.list_transcripts()
        
        # Load transcript
        content = manager.load("transcript_20240115.txt")
    """
    
    def __init__(
        self,
        output_dir: Union[str, Path] = None,
        auto_create: bool = True
    ):
        """
        Initialize output manager.
        
        Args:
            output_dir: Directory for transcripts. Default: output/transcripts
            auto_create: Create directory if not exists
        """
        if output_dir is None:
            output_dir = PROJECT_ROOT / "output" / "transcripts"
        
        self.output_dir = Path(output_dir)
        self.formatter = OutputFormatter()
        
        if auto_create:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, prefix: str = "transcript", ext: str = "txt") -> str:
        """Generate unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{ext}"
    
    def save(
        self,
        text: str,
        format: str = "txt",
        filename: Optional[str] = None,
        overwrite: bool = False,
        **kwargs
    ) -> SavedTranscript:
        """
        Save transcription to file.
        
        Args:
            text: Transcription text
            format: Output format (txt, json, srt, vtt)
            filename: Custom filename (without extension)
            overwrite: Overwrite if exists
            **kwargs: Additional metadata for formatter
            
        Returns:
            SavedTranscript object
        """
        format = format.lower()
        
        # Determine filename
        if filename:
            # Remove extension if provided
            filename = Path(filename).stem
            full_filename = f"{filename}.{format}"
        else:
            full_filename = self._generate_filename(ext=format)
        
        filepath = self.output_dir / full_filename
        
        # Check overwrite
        if filepath.exists() and not overwrite:
            # Add suffix to avoid overwrite
            counter = 1
            base_name = filepath.stem
            while filepath.exists():
                full_filename = f"{base_name}_{counter}.{format}"
                filepath = self.output_dir / full_filename
                counter += 1
        
        # Format content
        formatted = self.formatter.format(text, format, **kwargs)
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted)
        
        # Get file info
        stat = filepath.stat()
        
        return SavedTranscript(
            filepath=str(filepath),
            filename=full_filename,
            format=format,
            size_bytes=stat.st_size,
            created_at=datetime.now().isoformat()
        )
    
    def save_multiple_formats(
        self,
        text: str,
        formats: List[str] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> List[SavedTranscript]:
        """
        Save transcription in multiple formats.
        
        Args:
            text: Transcription text
            formats: List of formats. Default: ["txt", "json"]
            filename: Base filename (without extension)
            **kwargs: Additional metadata
            
        Returns:
            List of SavedTranscript objects
        """
        if formats is None:
            formats = ["txt", "json"]
        
        results = []
        for fmt in formats:
            result = self.save(text, format=fmt, filename=filename, **kwargs)
            results.append(result)
        
        return results
    
    def save_from_result(
        self,
        result,
        format: str = "txt",
        filename: Optional[str] = None
    ) -> SavedTranscript:
        """
        Save from TranscriptionResult or LiveSTTResult object.
        
        Args:
            result: Result object with .text attribute
            format: Output format
            filename: Custom filename
            
        Returns:
            SavedTranscript object
        """
        # Extract metadata from result
        kwargs = {}
        
        if hasattr(result, "model"):
            kwargs["model"] = result.model
        if hasattr(result, "language"):
            kwargs["language"] = result.language
        if hasattr(result, "duration_sec"):
            kwargs["duration_sec"] = result.duration_sec
        if hasattr(result, "total_latency_sec"):
            kwargs["latency_sec"] = result.total_latency_sec
        if hasattr(result, "audio_path"):
            kwargs["source_file"] = result.audio_path
        if hasattr(result, "audio_file"):
            kwargs["source_file"] = result.audio_file
        if hasattr(result, "segments"):
            kwargs["segments"] = result.segments
        
        return self.save(result.text, format=format, filename=filename, **kwargs)
    
    def load(self, filename: str) -> str:
        """
        Load transcript content from file.
        
        Args:
            filename: Filename or full path
            
        Returns:
            File content as string
        """
        # Check if full path or just filename
        path = Path(filename)
        if not path.is_absolute():
            path = self.output_dir / filename
        
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON transcript as dictionary.
        
        Args:
            filename: JSON filename
            
        Returns:
            Dictionary with transcript data
        """
        content = self.load(filename)
        return json.loads(content)
    
    def list_transcripts(
        self,
        format_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[SavedTranscript]:
        """
        List saved transcripts.
        
        Args:
            format_filter: Filter by format (txt, json, etc.)
            limit: Maximum number of files to return
            
        Returns:
            List of SavedTranscript objects
        """
        transcripts = []
        
        if not self.output_dir.exists():
            return transcripts
        
        # Get all files
        files = list(self.output_dir.iterdir())
        
        # Filter by format
        if format_filter:
            files = [f for f in files if f.suffix == f".{format_filter}"]
        else:
            # Only include known formats
            valid_extensions = {".txt", ".json", ".srt", ".vtt"}
            files = [f for f in files if f.suffix in valid_extensions]
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Apply limit
        if limit:
            files = files[:limit]
        
        # Build result
        for f in files:
            stat = f.stat()
            transcripts.append(SavedTranscript(
                filepath=str(f),
                filename=f.name,
                format=f.suffix[1:],  # Remove leading dot
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))
        
        return transcripts
    
    def delete(self, filename: str) -> bool:
        """
        Delete a transcript file.
        
        Args:
            filename: Filename or full path
            
        Returns:
            True if deleted
        """
        path = Path(filename)
        if not path.is_absolute():
            path = self.output_dir / filename
        
        if path.exists():
            path.unlink()
            return True
        return False
    
    def clear_all(self, confirm: bool = False) -> int:
        """
        Delete all transcripts.
        
        Args:
            confirm: Must be True to proceed
            
        Returns:
            Number of files deleted
        """
        if not confirm:
            raise ValueError("Set confirm=True to delete all transcripts")
        
        count = 0
        for f in self.output_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about saved transcripts.
        
        Returns:
            Dictionary with stats
        """
        transcripts = self.list_transcripts()
        
        total_size = sum(t.size_bytes for t in transcripts)
        
        format_counts = {}
        for t in transcripts:
            format_counts[t.format] = format_counts.get(t.format, 0) + 1
        
        return {
            "total_files": len(transcripts),
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "format_counts": format_counts,
            "output_dir": str(self.output_dir)
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get manager configuration info."""
        return {
            "output_dir": str(self.output_dir),
            "output_dir_exists": self.output_dir.exists(),
            "supported_formats": self.formatter.SUPPORTED_FORMATS,
            "stats": self.get_stats()
        }


# ================================================================
# CLI INTERFACE
# ================================================================

def print_help():
    """Print detailed help."""
    help_text = """
================================================================================
SPEECHEE OUTPUT MANAGER - HELP
================================================================================

USAGE:
  python output_manager.py <command> [options]

COMMANDS:
  save          Save text to file
  load          Load transcript from file
  list          List saved transcripts
  stats         Show storage statistics
  delete        Delete a transcript
  info          Show manager info
  help          Show this help

OPTIONS:
  --text, -t    Text to save
  --format, -f  Output format (txt, json, srt, vtt)
  --name, -n    Custom filename (without extension)
  --file        File to load/delete
  --limit       Limit number of files listed
  --filter      Filter by format

EXAMPLES:
  # Save as text
  python output_manager.py save --text "Hello world" --format txt
  
  # Save as JSON with custom name
  python output_manager.py save --text "Hello world" --format json --name my_transcript
  
  # Save in multiple formats
  python output_manager.py save --text "Hello world" --format txt --format json
  
  # List transcripts
  python output_manager.py list
  python output_manager.py list --filter json --limit 5
  
  # Load transcript
  python output_manager.py load --file transcript_20240115.txt
  
  # Delete transcript
  python output_manager.py delete --file transcript_20240115.txt
  
  # Show stats
  python output_manager.py stats

================================================================================
"""
    print(help_text)


def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Output Manager",
        add_help=False
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["save", "load", "list", "stats", "delete", "info", "help"],
        default="help",
        help="Command to execute"
    )
    parser.add_argument("--text", "-t", help="Text to save")
    parser.add_argument(
        "--format", "-f",
        action="append",
        choices=["txt", "json", "srt", "vtt"],
        help="Output format(s)"
    )
    parser.add_argument("--name", "-n", help="Custom filename")
    parser.add_argument("--file", help="File to load/delete")
    parser.add_argument("--limit", type=int, help="Limit results")
    parser.add_argument("--filter", help="Filter by format")
    parser.add_argument("--model", "-m", help="Model name for metadata")
    parser.add_argument("--duration", "-d", type=float, help="Duration for metadata")
    parser.add_argument("--help", "-h", action="store_true", help="Show help")
    
    args = parser.parse_args()
    
    if args.help or args.command == "help":
        print_help()
        return
    
    manager = OutputManager()
    
    if args.command == "save":
        if not args.text:
            print("[ERROR] Text required. Use --text 'your text'")
            sys.exit(1)
        
        formats = args.format or ["txt"]
        kwargs = {}
        if args.model:
            kwargs["model"] = args.model
        if args.duration:
            kwargs["duration_sec"] = args.duration
        
        if len(formats) == 1:
            result = manager.save(args.text, format=formats[0], filename=args.name, **kwargs)
            print(f"\n[SUCCESS] Saved transcript")
            print(f"  File: {result.filename}")
            print(f"  Path: {result.filepath}")
            print(f"  Size: {result.size_bytes} bytes")
        else:
            results = manager.save_multiple_formats(args.text, formats=formats, filename=args.name, **kwargs)
            print(f"\n[SUCCESS] Saved {len(results)} files:")
            for r in results:
                print(f"  - {r.filename} ({r.size_bytes} bytes)")
    
    elif args.command == "load":
        if not args.file:
            print("[ERROR] File required. Use --file filename")
            sys.exit(1)
        
        try:
            content = manager.load(args.file)
            print(f"\n{'='*60}")
            print(f"FILE: {args.file}")
            print('='*60)
            print(content)
            print('='*60)
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    
    elif args.command == "list":
        transcripts = manager.list_transcripts(
            format_filter=args.filter,
            limit=args.limit
        )
        
        print("\n" + "=" * 70)
        print("SAVED TRANSCRIPTS")
        print("=" * 70)
        
        if not transcripts:
            print("\n  No transcripts found.")
        else:
            print(f"\n{'Filename':<40} {'Format':<8} {'Size':<12} {'Created':<20}")
            print("-" * 70)
            for t in transcripts:
                size_str = f"{t.size_bytes} B" if t.size_bytes < 1024 else f"{t.size_bytes/1024:.1f} KB"
                created = t.created_at.split("T")[0]
                print(f"{t.filename:<40} {t.format:<8} {size_str:<12} {created:<20}")
        
        print("=" * 70)
    
    elif args.command == "stats":
        stats = manager.get_stats()
        
        print("\n" + "=" * 50)
        print("TRANSCRIPT STATISTICS")
        print("=" * 50)
        print(f"\n  Total Files:  {stats['total_files']}")
        print(f"  Total Size:   {stats['total_size_kb']} KB")
        print(f"  Output Dir:   {stats['output_dir']}")
        print(f"\n  By Format:")
        for fmt, count in stats['format_counts'].items():
            print(f"    {fmt}: {count} files")
        print("=" * 50)
    
    elif args.command == "delete":
        if not args.file:
            print("[ERROR] File required. Use --file filename")
            sys.exit(1)
        
        if manager.delete(args.file):
            print(f"[SUCCESS] Deleted: {args.file}")
        else:
            print(f"[ERROR] File not found: {args.file}")
    
    elif args.command == "info":
        info = manager.get_info()
        
        print("\n" + "=" * 50)
        print("OUTPUT MANAGER INFO")
        print("=" * 50)
        print(f"\n  Output Dir: {info['output_dir']}")
        print(f"  Exists: {info['output_dir_exists']}")
        print(f"  Formats: {', '.join(info['supported_formats'])}")
        print(f"\n  Files: {info['stats']['total_files']}")
        print(f"  Size: {info['stats']['total_size_kb']} KB")
        print("=" * 50)
    
    else:
        print_help()


if __name__ == "__main__":
    main()