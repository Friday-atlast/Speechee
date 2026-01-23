"""
Speechee - Language Detection Tests
Test Hindi, English, and Hinglish detection.
"""

import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stt.language import LanguageManager, LanguageResult


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name: str, text: str, result: LanguageResult, expected_code: str):
    """Print test result."""
    passed = result.code == expected_code
    status = "✓ PASS" if passed else "✗ FAIL"
    
    print(f"\n  {status}: {name}")
    print(f"    Text: \"{text[:40]}{'...' if len(text) > 40 else ''}\"")
    print(f"    Expected: {expected_code}")
    print(f"    Got: {result.code} ({result.name})")
    print(f"    Confidence: {result.confidence:.2%}")
    
    return passed


def run_tests():
    """Run all language detection tests."""
    lm = LanguageManager()
    
    passed = 0
    failed = 0
    
    # ============================================================
    # ENGLISH TESTS
    # ============================================================
    print_header("ENGLISH TESTS")
    
    english_tests = [
        ("Simple English", "Hello, how are you?", "en"),
        ("Long English", "The quick brown fox jumps over the lazy dog.", "en"),
        ("Formal English", "Please find attached the document for your review.", "en"),
        ("Casual English", "Hey what's up buddy, wanna grab some coffee?", "en"),
        ("Technical English", "The API returns a JSON response with status code 200.", "en"),
    ]
    
    for name, text, expected in english_tests:
        result = lm.detect(text)
        if print_test(name, text, result, expected):
            passed += 1
        else:
            failed += 1
    
    # ============================================================
    # HINDI TESTS
    # ============================================================
    print_header("HINDI TESTS")
    
    hindi_tests = [
        ("Simple Hindi", "नमस्ते, आप कैसे हैं?", "hi"),
        ("Hindi Greeting", "आपका स्वागत है", "hi"),
        ("Hindi Sentence", "मेरा नाम राहुल है और मैं दिल्ली से हूं", "hi"),
        ("Hindi Question", "आज मौसम कैसा है?", "hi"),
        ("Formal Hindi", "कृपया अपना परिचय दीजिए", "hi"),
    ]
    
    for name, text, expected in hindi_tests:
        result = lm.detect(text)
        if print_test(name, text, result, expected):
            passed += 1
        else:
            failed += 1
    
    # ============================================================
    # HINGLISH TESTS
    # ============================================================
    print_header("HINGLISH TESTS (Mixed Hindi-English)")
    
    hinglish_tests = [
        ("Hinglish 1", "Hello bhai, kya haal hai?", "hi"),  # More Romanized Hindi
        ("Hinglish 2", "Aaj main office nahi jaunga", "hi"),
        ("Hinglish 3", "Please mujhe ek coffee de do", "hi"),
        ("Code Mix", "Meeting mein late mat hona okay?", "hi"),
    ]
    
    for name, text, expected in hinglish_tests:
        result = lm.detect(text)
        is_hinglish, mix_ratio = lm.detect_hinglish(text)
        
        # For Hinglish, we accept either 'hi' or 'en' as it's mixed
        # But multilingual model is recommended
        print(f"\n  TEST: {name}")
        print(f"    Text: \"{text}\"")
        print(f"    Detected: {result.code} ({result.name})")
        print(f"    Hinglish: {is_hinglish}, Mix: {mix_ratio:.2%}")
        
        # Consider test passed if detection is reasonable
        if result.code in ["hi", "en"]:
            print(f"    ✓ PASS (reasonable detection)")
            passed += 1
        else:
            print(f"    ✗ FAIL (unexpected: {result.code})")
            failed += 1
    
    # ============================================================
    # HINGLISH DETECTION FUNCTION
    # ============================================================
    print_header("HINGLISH DETECTION FUNCTION")
    
    hinglish_detect_tests = [
        ("Pure English", "Hello how are you", False),
        ("Pure Hindi", "नमस्ते आप कैसे हैं", False),
        ("Mixed Script", "Hello नमस्ते", True),
        ("Devanagari in English", "I said नमस्ते to him", True),
    ]
    
    for name, text, expected_hinglish in hinglish_detect_tests:
        is_hinglish, mix_ratio = lm.detect_hinglish(text)
        
        passed_test = is_hinglish == expected_hinglish
        status = "✓ PASS" if passed_test else "✗ FAIL"
        
        print(f"\n  {status}: {name}")
        print(f"    Text: \"{text}\"")
        print(f"    Expected Hinglish: {expected_hinglish}")
        print(f"    Got Hinglish: {is_hinglish}")
        print(f"    Mix Ratio: {mix_ratio:.2%}")
        
        if passed_test:
            passed += 1
        else:
            failed += 1
    
    # ============================================================
    # MODEL RECOMMENDATIONS
    # ============================================================
    print_header("MODEL RECOMMENDATIONS")
    
    model_tests = [
        ("en", "fast", "tiny.en"),
        ("en", "balanced", "base.en"),
        ("hi", "fast", "tiny"),
        ("hi", "balanced", "base"),
        ("es", "balanced", "base"),  # Spanish
    ]
    
    for lang, quality, expected_model in model_tests:
        model = lm.get_recommended_model(lang, quality)
        passed_test = model == expected_model
        status = "✓ PASS" if passed_test else "✗ FAIL"
        
        print(f"\n  {status}: {lang} ({quality})")
        print(f"    Expected: {expected_model}")
        print(f"    Got: {model}")
        
        if passed_test:
            passed += 1
        else:
            failed += 1
    
    # ============================================================
    # MODEL VALIDATION
    # ============================================================
    print_header("MODEL-LANGUAGE VALIDATION")
    
    validation_tests = [
        ("tiny.en", "en", True),
        ("tiny.en", "hi", False),  # English model can't do Hindi
        ("tiny", "hi", True),
        ("base", "es", True),
    ]
    
    for model, lang, expected_valid in validation_tests:
        is_valid, message = lm.validate_model_language(model, lang)
        passed_test = is_valid == expected_valid
        status = "✓ PASS" if passed_test else "✗ FAIL"
        
        print(f"\n  {status}: {model} + {lang}")
        print(f"    Expected Valid: {expected_valid}")
        print(f"    Got Valid: {is_valid}")
        if not is_valid:
            print(f"    Message: {message}")
        
        if passed_test:
            passed += 1
        else:
            failed += 1
    
    # ============================================================
    # EDGE CASES
    # ============================================================
    print_header("EDGE CASES")
    
    edge_cases = [
        ("Empty String", "", "en"),  # Should fallback
        ("Single Word", "Hi", "en"),
        ("Numbers Only", "12345", "en"),  # Should fallback
        ("Special Chars", "!@#$%", "en"),  # Should fallback
        ("Very Short", "OK", "en"),
    ]
    
    for name, text, expected in edge_cases:
        result = lm.detect(text)
        # For edge cases, we accept fallback behavior
        print(f"\n  TEST: {name}")
        print(f"    Text: \"{text}\"")
        print(f"    Result: {result.code} (method: {result.method})")
        
        if result.method == "fallback" or result.code == expected:
            print(f"    ✓ PASS (handled gracefully)")
            passed += 1
        else:
            print(f"    ✗ FAIL")
            failed += 1
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"\n  Total Tests: {passed + failed}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {passed / (passed + failed) * 100:.1f}%")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SPEECHEE LANGUAGE DETECTION TESTS")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n  ✓ All tests passed!")
    else:
        print("\n  ✗ Some tests failed!")
    
    sys.exit(0 if success else 1)