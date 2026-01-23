"""
Speechee - Language Manager
Multi-language detection and handling.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Language detection library
try:
    from langdetect import detect, detect_langs, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    detect = None
    detect_langs = None
    LangDetectException = Exception


@dataclass
class LanguageResult:
    """Result of language detection."""
    code: str               # ISO 639-1 code (en, hi, etc.)
    name: str               # Full name (English, Hindi)
    confidence: float       # 0.0 to 1.0
    method: str             # "auto", "manual", "fallback"
    alternatives: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "confidence": self.confidence,
            "method": self.method,
            "alternatives": self.alternatives
        }


class LanguageManager:
    """
    Manage language detection and selection.
    
    Features:
    - Auto-detect language from text
    - Manual language override
    - Whisper-compatible language codes
    - Model recommendation based on language
    
    Usage:
        lm = LanguageManager()
        
        # Auto-detect
        result = lm.detect("Hello, how are you?")
        print(result.code)  # "en"
        
        # Detect Hindi
        result = lm.detect("नमस्ते, आप कैसे हैं?")
        print(result.code)  # "hi"
        
        # Get recommended model
        model = lm.get_recommended_model("hi")
        print(model)  # "tiny" (multilingual)
    """
    
    # Whisper supported languages (subset)
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "tr": "Turkish",
        "pl": "Polish",
        "nl": "Dutch",
        "sv": "Swedish",
        "ta": "Tamil",
        "te": "Telugu",
        "mr": "Marathi",
        "bn": "Bengali",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "ur": "Urdu",
    }
    
    # English-only models
    ENGLISH_MODELS = ["tiny.en", "base.en", "small.en", "medium.en"]
    
    # Multilingual models
    MULTILINGUAL_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    # Model recommendations by language
    MODEL_RECOMMENDATIONS = {
        "en": {
            "fast": "tiny.en",
            "balanced": "base.en",
            "accurate": "small.en"
        },
        "hi": {
            "fast": "tiny",
            "balanced": "base",
            "accurate": "small"
        },
        "default": {
            "fast": "tiny",
            "balanced": "base",
            "accurate": "small"
        }
    }
    
    def __init__(self, default_language: str = "auto"):
        """
        Initialize language manager.
        
        Args:
            default_language: Default language code or "auto"
        """
        self.default_language = default_language
        self._validate_library()
    
    def _validate_library(self) -> None:
        """Check if langdetect is available."""
        if not HAS_LANGDETECT:
            print("[WARN] langdetect not installed. Install: pip install langdetect")
    
    def detect(
    self,
    text: str,
    fallback: str = "en"
    ) -> LanguageResult:
        """
        Detect language of text with Hinglish support.
        
        Args:
            text: Text to analyze
            fallback: Fallback language if detection fails
            
        Returns:
            LanguageResult object
        """
        # 1. Clean and validate text
        text = text.strip()
        if not text or len(text) < 3:
            return LanguageResult(
                code=fallback,
                name=self.SUPPORTED_LANGUAGES.get(fallback, "Unknown"),
                confidence=0.0,
                method="fallback",
                alternatives=[]
            )
        
        # 2. Check for mixed scripts first (Hinglish detection)
        is_mixed, script_info = self.detect_hinglish(text)
        if is_mixed:
            # If mixed script detected, use fallback logic (better for Hinglish)
            return self._fallback_detection(text, fallback)
        
        # 3. No detection library available
        if not HAS_LANGDETECT:
            return self._fallback_detection(text, fallback)
        
        # 4. Use langdetect for longer texts
        try:
            detected = detect_langs(text)
            
            if not detected:
                return self._create_fallback_result(fallback)
            
            # Primary detection
            primary = detected[0]
            code = str(primary.lang)
            confidence = float(primary.prob)
            
            # Only trust langdetect if high confidence (>0.8) OR text is long enough
            if confidence < 0.8 and len(text) < 20:
                return self._fallback_detection(text, fallback)
            
            # Map to supported language if needed
            if code not in self.SUPPORTED_LANGUAGES:
                code = self._map_language_code(code, fallback)
            
            # Build alternatives list (top 3)
            alternatives = []
            for lang in detected[1:4]:
                alt_code = str(lang.lang)
                if alt_code in self.SUPPORTED_LANGUAGES:
                    alternatives.append({
                        "code": alt_code,
                        "name": self.SUPPORTED_LANGUAGES[alt_code],
                        "confidence": float(lang.prob)
                    })
            
            return LanguageResult(
                code=code,
                name=self.SUPPORTED_LANGUAGES.get(code, "Unknown"),
                confidence=confidence,
                method="auto",
                alternatives=alternatives
            )
            
        except LangDetectException:
            return self._create_fallback_result(fallback)
        except Exception as e:
            print(f"[WARN] Language detection error: {e}")
            return self._create_fallback_result(fallback)
    
    def _fallback_detection(self, text: str, fallback: str) -> LanguageResult:
        """Simple fallback detection using character analysis."""
        # Check for Devanagari (Hindi)
        devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        # Check for ASCII (likely English)
        ascii_count = sum(1 for c in text if c.isascii() and c.isalpha())
        
        total = len(text.replace(" ", ""))
        
        if total == 0:
            return self._create_fallback_result(fallback)
        
        devanagari_ratio = devanagari_count / total
        ascii_ratio = ascii_count / total
        
        if devanagari_ratio > 0.3:
            # Significant Hindi content
            if ascii_ratio > 0.2:
                # Mixed - Hinglish
                return LanguageResult(
                    code="hi",
                    name="Hindi (Hinglish)",
                    confidence=0.7,
                    method="fallback",
                    alternatives=[{
                        "code": "en",
                        "name": "English",
                        "confidence": ascii_ratio
                    }]
                )
            else:
                return LanguageResult(
                    code="hi",
                    name="Hindi",
                    confidence=devanagari_ratio,
                    method="fallback",
                    alternatives=[]
                )
        elif ascii_ratio > 0.5:
            return LanguageResult(
                code="en",
                name="English",
                confidence=ascii_ratio,
                method="fallback",
                alternatives=[]
            )
        else:
            return self._create_fallback_result(fallback)
    
    def _create_fallback_result(self, code: str) -> LanguageResult:
        """Create a fallback result."""
        return LanguageResult(
            code=code,
            name=self.SUPPORTED_LANGUAGES.get(code, "Unknown"),
            confidence=0.0,
            method="fallback",
            alternatives=[]
        )
    
    def _map_language_code(self, code: str, fallback: str) -> str:
        """Map unsupported code to closest supported language."""
        # Common mappings
        mappings = {
            "zh-cn": "zh",
            "zh-tw": "zh",
            "pt-br": "pt",
            "pt-pt": "pt",
        }
        
        if code in mappings:
            return mappings[code]
        
        # Try base code (e.g., "en-us" -> "en")
        base = code.split("-")[0]
        if base in self.SUPPORTED_LANGUAGES:
            return base
        
        return fallback
    
    def is_supported(self, code: str) -> bool:
        """Check if language is supported."""
        return code in self.SUPPORTED_LANGUAGES or code == "auto"
    
    def get_language_name(self, code: str) -> str:
        """Get full language name from code."""
        return self.SUPPORTED_LANGUAGES.get(code, "Unknown")
    
    def get_recommended_model(
        self,
        language: str = "en",
        quality: str = "balanced"
    ) -> str:
        """
        Get recommended Whisper model for language.
        
        Args:
            language: Language code
            quality: "fast", "balanced", or "accurate"
            
        Returns:
            Model name
        """
        # Get language-specific recommendations
        if language in self.MODEL_RECOMMENDATIONS:
            recs = self.MODEL_RECOMMENDATIONS[language]
        else:
            recs = self.MODEL_RECOMMENDATIONS["default"]
        
        return recs.get(quality, recs["balanced"])
    
    def requires_multilingual_model(self, language: str) -> bool:
        """Check if language requires multilingual model."""
        return language != "en" and language != "auto"
    
    def validate_model_language(self, model: str, language: str) -> Tuple[bool, str]:
        """
        Validate if model supports the language.
        
        Args:
            model: Model name
            language: Language code
            
        Returns:
            (is_valid, message)
        """
        is_english_model = model in self.ENGLISH_MODELS or model.endswith(".en")
        is_english_language = language == "en"
        
        if is_english_model and not is_english_language and language != "auto":
            return False, f"Model '{model}' only supports English. Use multilingual model for {language}."
        
        return True, "OK"
    
    def detect_hinglish(self, text: str) -> Tuple[bool, float]:
        """
        Detect if text is Hinglish (mixed Hindi-English).
        
        Args:
            text: Text to analyze
            
        Returns:
            (is_hinglish, mix_ratio)
        """
        if not text:
            return False, 0.0
        
        # Count Devanagari characters
        devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        # Count ASCII letters
        ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
        
        total = devanagari + ascii_letters
        
        if total == 0:
            return False, 0.0
        
        hindi_ratio = devanagari / total
        english_ratio = ascii_letters / total
        
        # Hinglish: significant mix of both
        is_hinglish = hindi_ratio > 0.1 and english_ratio > 0.1
        mix_ratio = min(hindi_ratio, english_ratio) * 2  # 0 to 1
        
        return is_hinglish, mix_ratio
    
    def get_all_languages(self) -> Dict[str, str]:
        """Get all supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def print_languages(self) -> None:
        """Print all supported languages."""
        print("\n" + "=" * 50)
        print("SUPPORTED LANGUAGES")
        print("=" * 50)
        print(f"\n{'Code':<8} {'Language':<20}")
        print("-" * 50)
        for code, name in sorted(self.SUPPORTED_LANGUAGES.items()):
            print(f"{code:<8} {name:<20}")
        print("=" * 50)


# ================================================================
# CLI INTERFACE
# ================================================================

def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speechee Language Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python language.py detect "Hello, how are you?"
  python language.py detect "नमस्ते, आप कैसे हैं?"
  python language.py detect "Hello bhai, kya haal hai?"
  python language.py list
  python language.py model hi
  python language.py model en --quality accurate
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Detect language")
    detect_parser.add_argument("text", help="Text to analyze")
    detect_parser.add_argument("--fallback", "-f", default="en", help="Fallback language")
    
    # List command
    subparsers.add_parser("list", help="List supported languages")
    
    # Model command
    model_parser = subparsers.add_parser("model", help="Get recommended model")
    model_parser.add_argument("language", help="Language code")
    model_parser.add_argument("--quality", "-q", choices=["fast", "balanced", "accurate"], default="balanced")
    
    # Hinglish command
    hinglish_parser = subparsers.add_parser("hinglish", help="Check for Hinglish")
    hinglish_parser.add_argument("text", help="Text to analyze")
    
    args = parser.parse_args()
    lm = LanguageManager()
    
    if args.command == "detect":
        result = lm.detect(args.text, fallback=args.fallback)
        
        print("\n" + "=" * 50)
        print("LANGUAGE DETECTION RESULT")
        print("=" * 50)
        print(f"\n  Text: \"{args.text[:50]}{'...' if len(args.text) > 50 else ''}\"")
        print(f"\n  Detected: {result.name} ({result.code})")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Method: {result.method}")
        
        if result.alternatives:
            print(f"\n  Alternatives:")
            for alt in result.alternatives:
                print(f"    - {alt['name']} ({alt['code']}): {alt['confidence']:.2%}")
        
        # Check for Hinglish
        is_hinglish, mix_ratio = lm.detect_hinglish(args.text)
        if is_hinglish:
            print(f"\n  ⚠ Detected as Hinglish (mix ratio: {mix_ratio:.2%})")
        
        print("\n" + "=" * 50)
    
    elif args.command == "list":
        lm.print_languages()
    
    elif args.command == "model":
        model = lm.get_recommended_model(args.language, args.quality)
        requires_multi = lm.requires_multilingual_model(args.language)
        
        print(f"\n  Language: {lm.get_language_name(args.language)} ({args.language})")
        print(f"  Quality: {args.quality}")
        print(f"  Recommended Model: {model}")
        print(f"  Requires Multilingual: {requires_multi}")
    
    elif args.command == "hinglish":
        is_hinglish, mix_ratio = lm.detect_hinglish(args.text)
        result = lm.detect(args.text)
        
        print("\n" + "=" * 50)
        print("HINGLISH ANALYSIS")
        print("=" * 50)
        print(f"\n  Text: \"{args.text}\"")
        print(f"\n  Is Hinglish: {'Yes' if is_hinglish else 'No'}")
        print(f"  Mix Ratio: {mix_ratio:.2%}")
        print(f"  Primary Language: {result.name} ({result.code})")
        print(f"\n  Recommendation: Use multilingual model ('tiny' or 'base')")
        print("=" * 50)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()