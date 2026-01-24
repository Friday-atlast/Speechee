#!/usr/bin/env python3
"""
Speechee - Resource Monitor
Monitor CPU, RAM usage during transcription.
Provided by Friday
"""

import os
import sys
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("[WARN] psutil not installed. Run: pip install psutil")

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ResourceSnapshot:
    """Single resource measurement."""
    timestamp: float
    cpu_percent: float
    ram_mb: float
    ram_percent: float


@dataclass
class MonitoringResult:
    """Complete monitoring session result."""
    duration_sec: float
    snapshots: List[ResourceSnapshot]
    peak_cpu: float
    peak_ram_mb: float
    avg_cpu: float
    avg_ram_mb: float
    passed_ram_limit: bool
    ram_limit_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_sec": round(self.duration_sec, 2),
            "peak_cpu": round(self.peak_cpu, 1),
            "peak_ram_mb": round(self.peak_ram_mb, 1),
            "avg_cpu": round(self.avg_cpu, 1),
            "avg_ram_mb": round(self.avg_ram_mb, 1),
            "passed_ram_limit": self.passed_ram_limit,
            "ram_limit_mb": self.ram_limit_mb,
            "snapshot_count": len(self.snapshots)
        }
    
    def print_summary(self):
        """Print formatted summary."""
        print("\n" + "=" * 50)
        print("📊 RESOURCE MONITORING SUMMARY")
        print("=" * 50)
        print(f"\n  Duration:     {self.duration_sec:.2f}s")
        print(f"  Snapshots:    {len(self.snapshots)}")
        print(f"\n  CPU:")
        print(f"    Peak:       {self.peak_cpu:.1f}%")
        print(f"    Average:    {self.avg_cpu:.1f}%")
        print(f"\n  RAM:")
        print(f"    Peak:       {self.peak_ram_mb:.1f} MB")
        print(f"    Average:    {self.avg_ram_mb:.1f} MB")
        print(f"    Limit:      {self.ram_limit_mb:.1f} MB")
        
        if self.passed_ram_limit:
            print(f"\n  ✅ RAM usage within limit!")
        else:
            print(f"\n  ❌ RAM exceeded limit!")
        
        print("=" * 50)


class ResourceMonitor:
    """
    Monitor system resources during transcription.
    
    Usage:
        monitor = ResourceMonitor(ram_limit_mb=1000)
        
        # Start monitoring in background
        monitor.start()
        
        # ... do transcription ...
        
        # Stop and get results
        result = monitor.stop()
        result.print_summary()
    """
    
    def __init__(
        self,
        interval_sec: float = 0.5,
        ram_limit_mb: float = 1000
    ):
        """
        Initialize monitor.
        
        Args:
            interval_sec: Sampling interval
            ram_limit_mb: RAM limit for pass/fail check (default 1GB)
        """
        if not HAS_PSUTIL:
            raise ImportError("psutil required: pip install psutil")
        
        self.interval = interval_sec
        self.ram_limit_mb = ram_limit_mb
        self.snapshots: List[ResourceSnapshot] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.process = psutil.Process(os.getpid())
        self.start_time = None
    
    def _collect_snapshot(self) -> ResourceSnapshot:
        """Collect single resource snapshot."""
        # Get process-specific memory
        mem_info = self.process.memory_info()
        ram_mb = mem_info.rss / (1024 * 1024)
        
        # Get system memory percentage
        system_mem = psutil.virtual_memory()
        ram_percent = (mem_info.rss / system_mem.total) * 100
        
        # Get CPU (process-specific)
        cpu_percent = self.process.cpu_percent()
        
        return ResourceSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            ram_mb=ram_mb,
            ram_percent=ram_percent
        )
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                snapshot = self._collect_snapshot()
                self.snapshots.append(snapshot)
            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
            time.sleep(self.interval)
    
    def start(self):
        """Start background monitoring."""
        if self.running:
            return
        
        self.snapshots = []
        self.running = True
        self.start_time = time.time()
        
        # Prime CPU measurement
        self.process.cpu_percent()
        
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> MonitoringResult:
        """Stop monitoring and return results."""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        if not self.snapshots:
            return MonitoringResult(
                duration_sec=duration,
                snapshots=[],
                peak_cpu=0,
                peak_ram_mb=0,
                avg_cpu=0,
                avg_ram_mb=0,
                passed_ram_limit=True,
                ram_limit_mb=self.ram_limit_mb
            )
        
        cpu_values = [s.cpu_percent for s in self.snapshots]
        ram_values = [s.ram_mb for s in self.snapshots]
        
        peak_ram = max(ram_values)
        
        return MonitoringResult(
            duration_sec=duration,
            snapshots=self.snapshots,
            peak_cpu=max(cpu_values),
            peak_ram_mb=peak_ram,
            avg_cpu=sum(cpu_values) / len(cpu_values),
            avg_ram_mb=sum(ram_values) / len(ram_values),
            passed_ram_limit=peak_ram <= self.ram_limit_mb,
            ram_limit_mb=self.ram_limit_mb
        )
    
    def get_current(self) -> Dict[str, float]:
        """Get current resource usage."""
        snapshot = self._collect_snapshot()
        return {
            "cpu_percent": round(snapshot.cpu_percent, 1),
            "ram_mb": round(snapshot.ram_mb, 1),
            "ram_percent": round(snapshot.ram_percent, 1)
        }


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    
    return {
        "cpu": {
            "cores": cpu_count,
            "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
            "usage_percent": psutil.cpu_percent()
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent
        },
        "is_low_end": memory.total < 6 * (1024**3) or cpu_count <= 4
    }


def monitor_transcription(audio_path: str, model: str = "tiny", language: str = "auto") -> Dict[str, Any]:
    """
    Monitor a transcription and return results with resource usage.
    
    Usage:
        result = monitor_transcription("audio.wav", model="tiny", language="hi")
        print(result["text"])
        print(result["resources"]["peak_ram_mb"])
    """
    from stt import OfflineTranscriber
    
    monitor = ResourceMonitor(ram_limit_mb=1000)
    monitor.start()
    
    try:
        transcriber = OfflineTranscriber(
            model=model,
            language=language,
            translate=False,
            verbose=False
        )
        
        result = transcriber.transcribe(audio_path)
        
    finally:
        resources = monitor.stop()
    
    return {
        "success": result.success,
        "text": result.text,
        "language": result.language,
        "model": result.model,
        "processing_time_sec": result.processing_time_sec,
        "resources": resources.to_dict(),
        "passed_optimization": resources.passed_ram_limit
    }


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Resource Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show system info
  python monitor.py system
  
  # Monitor current usage
  python monitor.py current
  
  # Monitor a transcription
  python monitor.py transcribe audio.wav --model tiny --language hi
  
  # Benchmark with RAM limit check
  python monitor.py transcribe audio.wav --ram-limit 800
        """
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # System info command
    subparsers.add_parser("system", help="Show system information")
    
    # Current usage command
    subparsers.add_parser("current", help="Show current resource usage")
    
    # Transcribe with monitoring
    trans_parser = subparsers.add_parser("transcribe", help="Monitor transcription")
    trans_parser.add_argument("audio", help="Audio file path")
    trans_parser.add_argument("--model", "-m", default="tiny", help="Model (default: tiny)")
    trans_parser.add_argument("--language", "-l", default="auto", help="Language (default: auto)")
    trans_parser.add_argument("--ram-limit", type=float, default=1000, help="RAM limit in MB (default: 1000)")
    
    args = parser.parse_args()
    
    if args.command == "system":
        info = get_system_info()
        print("\n" + "=" * 50)
        print("💻 SYSTEM INFORMATION")
        print("=" * 50)
        print(f"\n  CPU:")
        print(f"    Cores:     {info['cpu']['cores']}")
        print(f"    Frequency: {info['cpu']['frequency_mhz']} MHz")
        print(f"    Usage:     {info['cpu']['usage_percent']}%")
        print(f"\n  Memory:")
        print(f"    Total:     {info['memory']['total_gb']} GB")
        print(f"    Available: {info['memory']['available_gb']} GB")
        print(f"    Used:      {info['memory']['used_percent']}%")
        print(f"\n  Low-End Device: {'Yes' if info['is_low_end'] else 'No'}")
        print("=" * 50)
    
    elif args.command == "current":
        if not HAS_PSUTIL:
            print("[ERROR] psutil not installed")
            sys.exit(1)
        
        monitor = ResourceMonitor()
        current = monitor.get_current()
        
        print("\n" + "=" * 40)
        print("📊 CURRENT RESOURCE USAGE")
        print("=" * 40)
        print(f"\n  CPU:  {current['cpu_percent']}%")
        print(f"  RAM:  {current['ram_mb']} MB ({current['ram_percent']:.1f}%)")
        print("=" * 40)
    
    elif args.command == "transcribe":
        if not HAS_PSUTIL:
            print("[ERROR] psutil not installed")
            sys.exit(1)
        
        print(f"\n[MONITOR] Starting transcription with resource monitoring...")
        print(f"  Audio: {args.audio}")
        print(f"  Model: {args.model}")
        print(f"  Language: {args.language}")
        print(f"  RAM Limit: {args.ram_limit} MB")
        
        result = monitor_transcription(
            args.audio,
            model=args.model,
            language=args.language
        )
        
        print("\n" + "=" * 60)
        print("📝 TRANSCRIPTION RESULT")
        print("=" * 60)
        print(f"\n{result['text'][:500]}{'...' if len(result['text']) > 500 else ''}")
        print("\n" + "-" * 60)
        print(f"  Language:    {result['language']}")
        print(f"  Model:       {result['model']}")
        print(f"  Time:        {result['processing_time_sec']}s")
        print("-" * 60)
        print(f"  Peak CPU:    {result['resources']['peak_cpu']}%")
        print(f"  Peak RAM:    {result['resources']['peak_ram_mb']} MB")
        print(f"  Avg RAM:     {result['resources']['avg_ram_mb']} MB")
        print(f"  RAM Limit:   {result['resources']['ram_limit_mb']} MB")
        print("-" * 60)
        
        if result['passed_optimization']:
            print("  ✅ PASSED: RAM usage within limit!")
        else:
            print("  ❌ FAILED: RAM exceeded limit!")
        
        print("=" * 60)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()