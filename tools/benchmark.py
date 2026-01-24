#!/usr/bin/env python3
"""
Speechee - Performance Benchmark
Test transcription performance on low-end devices.
Provided by Friday
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def benchmark_models(audio_path: str) -> List[Dict[str, Any]]:
    """
    Benchmark all available models on a single audio file.
    
    Returns list of results with timing and resource info.
    """
    from stt import OfflineTranscriber
    from engine import EngineConfig
    from tools.monitor import ResourceMonitor
    
    downloaded = EngineConfig.list_downloaded_models()
    results = []
    
    print("\n" + "=" * 70)
    print("🏃 SPEECHEE MODEL BENCHMARK")
    print("=" * 70)
    print(f"\n  Audio: {audio_path}")
    print(f"  Models to test: {downloaded}")
    print("-" * 70)
    
    for model in downloaded:
        print(f"\n  Testing: {model}...")
        
        monitor = ResourceMonitor(ram_limit_mb=1000)
        monitor.start()
        
        try:
            transcriber = OfflineTranscriber(
                model=model,
                language="auto",
                translate=False,
                verbose=False
            )
            
            start = time.time()
            result = transcriber.transcribe(audio_path)
            elapsed = time.time() - start
            
            resources = monitor.stop()
            
            results.append({
                "model": model,
                "success": result.success,
                "text_length": len(result.text),
                "processing_time_sec": round(elapsed, 2),
                "peak_ram_mb": round(resources.peak_ram_mb, 1),
                "peak_cpu": round(resources.peak_cpu, 1),
                "passed": resources.passed_ram_limit
            })
            
            status = "✅" if resources.passed_ram_limit else "❌"
            print(f"    {status} Time: {elapsed:.2f}s | RAM: {resources.peak_ram_mb:.0f}MB | CPU: {resources.peak_cpu:.0f}%")
            
        except Exception as e:
            monitor.stop()
            results.append({
                "model": model,
                "success": False,
                "error": str(e),
                "passed": False
            })
            print(f"    ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"\n  {'Model':<12} {'Time':<10} {'RAM (MB)':<12} {'CPU %':<10} {'Status'}")
    print("-" * 70)
    
    for r in results:
        if r.get("success"):
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"  {r['model']:<12} {r['processing_time_sec']:<10} {r['peak_ram_mb']:<12} {r['peak_cpu']:<10} {status}")
        else:
            print(f"  {r['model']:<12} {'ERROR':<10} {'-':<12} {'-':<10} ❌ FAIL")
    
    print("=" * 70)
    
    # Recommendation
    passed = [r for r in results if r.get("passed") and r.get("success")]
    if passed:
        fastest = min(passed, key=lambda x: x["processing_time_sec"])
        lowest_ram = min(passed, key=lambda x: x["peak_ram_mb"])
        
        print(f"\n  💡 Recommendations for Low-End Devices:")
        print(f"     Fastest:    {fastest['model']} ({fastest['processing_time_sec']}s)")
        print(f"     Lowest RAM: {lowest_ram['model']} ({lowest_ram['peak_ram_mb']}MB)")
    
    print("=" * 70 + "\n")
    
    return results


def quick_test(audio_path: str = None) -> Dict[str, Any]:
    """
    Quick performance test with tiny model.
    """
    from tools.monitor import monitor_transcription, get_system_info
    
    # Use test audio if not provided
    if not audio_path:
        test_audio = PROJECT_ROOT / "tests" / "test_audio" / "jfk.wav"
        if not test_audio.exists():
            return {"error": "No test audio found. Provide audio path."}
        audio_path = str(test_audio)
    
    print("\n" + "=" * 50)
    print("⚡ QUICK PERFORMANCE TEST")
    print("=" * 50)
    
    # System info
    sys_info = get_system_info()
    print(f"\n  System: {sys_info['cpu']['cores']} cores, {sys_info['memory']['total_gb']}GB RAM")
    print(f"  Low-End: {'Yes' if sys_info['is_low_end'] else 'No'}")
    
    # Run test
    print(f"\n  Testing with 'tiny' model...")
    result = monitor_transcription(audio_path, model="tiny", language="auto")
    
    print(f"\n  Results:")
    print(f"    Time:     {result['processing_time_sec']}s")
    print(f"    Peak RAM: {result['resources']['peak_ram_mb']} MB")
    print(f"    Status:   {'✅ PASS' if result['passed_optimization'] else '❌ FAIL'}")
    
    print("=" * 50 + "\n")
    
    return result


# ================================================================
# CLI
# ================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Speechee Benchmark")
    parser.add_argument("command", choices=["quick", "full"], help="Test type")
    parser.add_argument("--audio", "-a", help="Audio file path")
    
    args = parser.parse_args()
    
    if args.command == "quick":
        quick_test(args.audio)
    elif args.command == "full":
        if not args.audio:
            test_audio = PROJECT_ROOT / "tests" / "test_audio" / "jfk.wav"
            if test_audio.exists():
                args.audio = str(test_audio)
            else:
                print("[ERROR] Provide audio file with --audio")
                sys.exit(1)
        benchmark_models(args.audio)