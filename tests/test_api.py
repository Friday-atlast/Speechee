#!/usr/bin/env python3
"""
Speechee API - Test Script
Tests all API endpoints.
"""

import sys
import time
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PROJECT_ROOT = Path(__file__).parent.parent
TEST_AUDIO = PROJECT_ROOT / "tests" / "test_audio" / "jfk.wav"


def print_result(name: str, passed: bool, detail: str = ""):
    """Print test result."""
    icon = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}{icon}{reset} {name}")
    if detail:
        print(f"      {detail}")
    return passed


def test_connection():
    """Test server connection."""
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        return r.status_code == 200
    except:
        return False


def run_tests():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("           SPEECHEE API TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Connection
    print("\n[Connection]")
    if not test_connection():
        print_result("Server Running", False, "Connection refused")
        print("\n❌ Server not running!")
        print("   Start with: python -m api.server")
        print("   Or: uvicorn api.server:app --reload")
        return
    results.append(print_result("Server Running", True))
    
    # Test 2: Root endpoint
    print("\n[System Endpoints]")
    try:
        r = requests.get(f"{BASE_URL}/")
        data = r.json()
        results.append(print_result("GET /", r.status_code == 200, f"name: {data.get('name')}"))
    except Exception as e:
        results.append(print_result("GET /", False, str(e)))
    
    # Test 3: Health endpoint
    try:
        r = requests.get(f"{BASE_URL}/health")
        data = r.json()
        results.append(print_result("GET /health", r.status_code == 200, 
                                   f"status: {data.get('status')}, models: {data.get('models_available')}"))
    except Exception as e:
        results.append(print_result("GET /health", False, str(e)))
    
    # Test 4: Swagger docs
    try:
        r = requests.get(f"{BASE_URL}/docs")
        results.append(print_result("GET /docs", r.status_code == 200, "Swagger UI accessible"))
    except Exception as e:
        results.append(print_result("GET /docs", False, str(e)))
    
    # Test 5: UI page
    try:
        r = requests.get(f"{BASE_URL}/ui")
        results.append(print_result("GET /ui", r.status_code == 200, "Landing page served"))
    except Exception as e:
        results.append(print_result("GET /ui", False, str(e)))
    
    # Test 6: Models endpoint
    print("\n[Data Endpoints]")
    try:
        r = requests.get(f"{BASE_URL}/models")
        data = r.json()
        results.append(print_result("GET /models", r.status_code == 200,
                                   f"total: {data.get('total')}, downloaded: {data.get('downloaded')}"))
    except Exception as e:
        results.append(print_result("GET /models", False, str(e)))
    
    # Test 7: Config endpoint
    try:
        r = requests.get(f"{BASE_URL}/config")
        results.append(print_result("GET /config", r.status_code == 200))
    except Exception as e:
        results.append(print_result("GET /config", False, str(e)))
    
    # Test 8: Devices endpoint
    try:
        r = requests.get(f"{BASE_URL}/devices")
        data = r.json()
        results.append(print_result("GET /devices", r.status_code == 200,
                                   f"found: {data.get('total')} devices"))
    except Exception as e:
        results.append(print_result("GET /devices", False, str(e)))
    
    # Test 9: Language detection
    try:
        r = requests.get(f"{BASE_URL}/language/detect", params={"text": "Hello world"})
        data = r.json()
        detected = data.get("detected", {})
        results.append(print_result("GET /language/detect", r.status_code == 200,
                                   f"detected: {detected.get('code')} ({detected.get('confidence'):.0%})"))
    except Exception as e:
        results.append(print_result("GET /language/detect", False, str(e)))
    
    # Test 10: STT endpoint (main transcription)
    print("\n[Transcription]")
    if TEST_AUDIO.exists():
        try:
            with open(TEST_AUDIO, "rb") as f:
                files = {"file": ("jfk.wav", f, "audio/wav")}
                data = {"model": "tiny.en", "language": "auto"}
                
                start = time.time()
                r = requests.post(f"{BASE_URL}/stt", files=files, data=data, timeout=120)
                elapsed = time.time() - start
            
            resp = r.json()
            success = r.status_code == 200 and resp.get("success")
            text_preview = resp.get("text", "")[:50]
            results.append(print_result("POST /stt", success,
                                       f"'{text_preview}...' ({elapsed:.1f}s)"))
        except Exception as e:
            results.append(print_result("POST /stt", False, str(e)))
    else:
        results.append(print_result("POST /stt", False, f"Test file not found: {TEST_AUDIO}"))
    
    # Test 11: Error handling (404)
    print("\n[Error Handling]")
    try:
        r = requests.get(f"{BASE_URL}/nonexistent")
        results.append(print_result("404 Handling", r.status_code == 404, "Returns 404 correctly"))
    except Exception as e:
        results.append(print_result("404 Handling", False, str(e)))
    
    # Test 12: Invalid file type
    try:
        files = {"file": ("test.txt", b"not audio", "text/plain")}
        r = requests.post(f"{BASE_URL}/stt", files=files)
        results.append(print_result("Invalid File Rejection", r.status_code == 400, "Rejects non-audio"))
    except Exception as e:
        results.append(print_result("Invalid File Rejection", False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    pct = (passed / total * 100) if total > 0 else 0
    
    print(f"  Results: {passed}/{total} passed ({pct:.0f}%)")
    
    if passed == total:
        print("  \033[92m✓ All tests passed!\033[0m")
    else:
        print(f"  \033[93m⚠ {total - passed} test(s) failed\033[0m")
    
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)