"""
Speechee - Output Formatter
Format transcription results into various output formats.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict


@dataclass
class TranscriptSegment:
    """A segment of transcription with timing."""
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start_time,
            "end": self.end_time,
            "text": self.text
        }


@dataclass
class FormattedOutput:
    """Formatted transcription output."""
    text: str
    format: str
    timestamp: str
    source_file: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    duration_sec: Optional[float] = None
    segments: Optional[List[TranscriptSegment]] = None
    metadata: Optional[Dict[str, Any]] = None


class OutputFormatter:
    """
    Format transcription results into various output formats.
    
    Supported formats:
    - txt: Plain text
    - json: JSON with metadata
    - srt: SubRip subtitle format
    - vtt: WebVTT subtitle format
    
    Usage:
        formatter = OutputFormatter()
        
        # Format as plain text
        txt = formatter.to_txt("Hello world")
        
        # Format as JSON
        json_str = formatter.to_json("Hello world", model="tiny.en")
        
        # Format as SRT
        srt = formatter.to_srt(segments)
    """
    
    SUPPORTED_FORMATS = ["txt", "json", "srt", "vtt"]
    
    def __init__(self):
        """Initialize formatter."""
        pass
    
    def format(
        self,
        text: str,
        output_format: str = "txt",
        **kwargs
    ) -> str:
        """
        Format text to specified format.
        
        Args:
            text: Transcription text
            output_format: Output format (txt, json, srt, vtt)
            **kwargs: Additional metadata
            
        Returns:
            Formatted string
        """
        output_format = output_format.lower()
        
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {output_format}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )
        
        if output_format == "txt":
            return self.to_txt(text, **kwargs)
        elif output_format == "json":
            return self.to_json(text, **kwargs)
        elif output_format == "srt":
            return self.to_srt(text, **kwargs)
        elif output_format == "vtt":
            return self.to_vtt(text, **kwargs)
    
    def to_txt(
        self,
        text: str,
        include_header: bool = False,
        **kwargs
    ) -> str:
        """
        Format as plain text.
        
        Args:
            text: Transcription text
            include_header: Include metadata header
            **kwargs: Additional metadata
            
        Returns:
            Plain text string
        """
        if not include_header:
            return text.strip()
        
        # Build header
        lines = []
        lines.append("=" * 60)
        lines.append("SPEECHEE TRANSCRIPTION")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if kwargs.get("model"):
            lines.append(f"Model: {kwargs['model']}")
        if kwargs.get("language"):
            lines.append(f"Language: {kwargs['language']}")
        if kwargs.get("duration_sec"):
            lines.append(f"Duration: {kwargs['duration_sec']:.2f}s")
        if kwargs.get("source_file"):
            lines.append(f"Source: {kwargs['source_file']}")
        
        lines.append("-" * 60)
        lines.append("")
        lines.append(text.strip())
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def to_json(
        self,
        text: str,
        pretty: bool = True,
        **kwargs
    ) -> str:
        """
        Format as JSON with metadata.
        
        Args:
            text: Transcription text
            pretty: Pretty print JSON
            **kwargs: Additional metadata
            
        Returns:
            JSON string
        """
        data = {
            "text": text.strip(),
            "timestamp": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        # Add optional metadata
        if kwargs.get("model"):
            data["model"] = kwargs["model"]
        if kwargs.get("language"):
            data["language"] = kwargs["language"]
        if kwargs.get("duration_sec"):
            data["duration_sec"] = kwargs["duration_sec"]
        if kwargs.get("source_file"):
            data["source_file"] = kwargs["source_file"]
        if kwargs.get("latency_sec"):
            data["latency_sec"] = kwargs["latency_sec"]
        
        # Add segments if available
        segments = kwargs.get("segments")
        if segments:
            if isinstance(segments, list):
                if segments and isinstance(segments[0], TranscriptSegment):
                    data["segments"] = [s.to_dict() for s in segments]
                else:
                    data["segments"] = segments
        
        # Add any extra metadata
        metadata = kwargs.get("metadata")
        if metadata:
            data["metadata"] = metadata
        
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    def to_srt(
        self,
        text: str,
        segments: Optional[List[TranscriptSegment]] = None,
        duration_sec: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Format as SRT subtitle.
        
        Args:
            text: Transcription text
            segments: Timed segments (if available)
            duration_sec: Total duration for auto-segmentation
            **kwargs: Additional metadata
            
        Returns:
            SRT formatted string
        """
        if segments:
            return self._segments_to_srt(segments)
        
        # Auto-segment if no segments provided
        if duration_sec is None:
            duration_sec = 10.0  # Default 10 seconds
        
        # Create single segment
        auto_segments = [
            TranscriptSegment(
                start_time=0.0,
                end_time=duration_sec,
                text=text.strip()
            )
        ]
        
        return self._segments_to_srt(auto_segments)
    
    def _segments_to_srt(self, segments: List[TranscriptSegment]) -> str:
        """Convert segments to SRT format."""
        lines = []
        
        for i, segment in enumerate(segments, 1):
            # Index
            lines.append(str(i))
            
            # Timestamps
            start = self._seconds_to_srt_time(segment.start_time)
            end = self._seconds_to_srt_time(segment.end_time)
            lines.append(f"{start} --> {end}")
            
            # Text
            lines.append(segment.text.strip())
            
            # Empty line separator
            lines.append("")
        
        return "\n".join(lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def to_vtt(
        self,
        text: str,
        segments: Optional[List[TranscriptSegment]] = None,
        duration_sec: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Format as WebVTT subtitle.
        
        Args:
            text: Transcription text
            segments: Timed segments (if available)
            duration_sec: Total duration for auto-segmentation
            **kwargs: Additional metadata
            
        Returns:
            VTT formatted string
        """
        # Start with WebVTT header
        lines = ["WEBVTT", ""]
        
        if segments:
            vtt_content = self._segments_to_vtt(segments)
        else:
            if duration_sec is None:
                duration_sec = 10.0
            
            auto_segments = [
                TranscriptSegment(
                    start_time=0.0,
                    end_time=duration_sec,
                    text=text.strip()
                )
            ]
            vtt_content = self._segments_to_vtt(auto_segments)
        
        lines.append(vtt_content)
        return "\n".join(lines)
    
    def _segments_to_vtt(self, segments: List[TranscriptSegment]) -> str:
        """Convert segments to VTT format."""
        lines = []
        
        for i, segment in enumerate(segments, 1):
            # Optional cue identifier
            lines.append(str(i))
            
            # Timestamps (VTT uses . instead of ,)
            start = self._seconds_to_vtt_time(segment.start_time)
            end = self._seconds_to_vtt_time(segment.end_time)
            lines.append(f"{start} --> {end}")
            
            # Text
            lines.append(segment.text.strip())
            
            # Empty line separator
            lines.append("")
        
        return "\n".join(lines)
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def from_live_result(self, result, output_format: str = "txt") -> str:
        """
        Format from LiveSTTResult object.
        
        Args:
            result: LiveSTTResult object
            output_format: Output format
            
        Returns:
            Formatted string
        """
        return self.format(
            text=result.text,
            output_format=output_format,
            model=result.model,
            duration_sec=result.duration_sec,
            latency_sec=result.total_latency_sec,
            source_file=result.audio_file
        )
    
    def from_transcription_result(self, result, output_format: str = "txt") -> str:
        """
        Format from TranscriptionResult object.
        
        Args:
            result: TranscriptionResult object
            output_format: Output format
            
        Returns:
            Formatted string
        """
        return self.format(
            text=result.text,
            output_format=output_format,
            model=result.model,
            language=result.language,
            source_file=result.audio_path,
            segments=result.segments
        )


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface for output formatting."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Speechee Output Formatter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formats:
  txt   Plain text output
  json  JSON with metadata
  srt   SubRip subtitle format
  vtt   WebVTT subtitle format

Examples:
  # Format text as JSON
  python formatter.py format "Hello world" --format json
  
  # Format with metadata
  python formatter.py format "Hello world" --format json --model tiny.en
  
  # Format as SRT with duration
  python formatter.py format "Hello world" --format srt --duration 5
  
  # Include header in text
  python formatter.py format "Hello world" --format txt --header

Supported Formats:
  txt, json, srt, vtt
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Format command
    fmt_parser = subparsers.add_parser("format", help="Format text")
    fmt_parser.add_argument("text", help="Text to format")
    fmt_parser.add_argument(
        "--format", "-f",
        choices=["txt", "json", "srt", "vtt"],
        default="txt",
        help="Output format (default: txt)"
    )
    fmt_parser.add_argument("--model", "-m", help="Model name for metadata")
    fmt_parser.add_argument("--language", "-l", help="Language code")
    fmt_parser.add_argument("--duration", "-d", type=float, help="Duration in seconds")
    fmt_parser.add_argument("--source", "-s", help="Source file path")
    fmt_parser.add_argument("--header", action="store_true", help="Include header (txt only)")
    fmt_parser.add_argument("--output", "-o", help="Output file path")
    
    # Formats command
    formats_parser = subparsers.add_parser("formats", help="List supported formats")
    
    args = parser.parse_args()
    
    if args.command == "format":
        formatter = OutputFormatter()
        
        kwargs = {}
        if args.model:
            kwargs["model"] = args.model
        if args.language:
            kwargs["language"] = args.language
        if args.duration:
            kwargs["duration_sec"] = args.duration
        if args.source:
            kwargs["source_file"] = args.source
        if args.header and args.format == "txt":
            kwargs["include_header"] = True
        
        try:
            result = formatter.format(args.text, args.format, **kwargs)
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"[SUCCESS] Saved to: {args.output}")
            else:
                print(result)
                
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    
    elif args.command == "formats":
        print("\n" + "=" * 40)
        print("SUPPORTED OUTPUT FORMATS")
        print("=" * 40)
        print("\n  txt  - Plain text")
        print("  json - JSON with metadata")
        print("  srt  - SubRip subtitle")
        print("  vtt  - WebVTT subtitle")
        print("\n" + "=" * 40)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()