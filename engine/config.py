"""
Speechee - Engine Configuration
Centralized configuration for model paths and engine settings.
"""

import os
from pathlib import Path


class EngineConfig:
    """Configuration class for Speechee STT engine."""
    
    # ================================================================
    # DIRECTORY PATHS
    # ================================================================
    
    ENGINE_DIR = Path(__file__).parent.resolve()
    PROJECT_DIR = ENGINE_DIR.parent
    MODELS_DIR = ENGINE_DIR / "models"
    WHISPER_CPP_DIR = ENGINE_DIR / "whisper.cpp"
    
    # Whisper.cpp binary (Windows - Visual Studio build)
    WHISPER_BINARY = WHISPER_CPP_DIR / "build" / "bin" / "Release" / "whisper-cli.exe"
    
    # ================================================================
    # MODEL CONFIGURATIONS
    # ================================================================
    
    MODELS = {
        # English-only models (faster, smaller)
        "tiny.en": {
            "filename": "ggml-tiny.en.bin",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
            "size_mb": 75,
            "ram_mb": 390,
            "language": "english",
            "speed": "fastest",
            "accuracy": "basic",
            "recommended_for": "low-end devices, quick tests"
        },
        
        # Multilingual models
        "tiny": {
            "filename": "ggml-tiny.bin",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
            "size_mb": 75,
            "ram_mb": 390,
            "language": "multilingual",
            "speed": "fastest",
            "accuracy": "basic",
            "recommended_for": "Hindi, Hinglish, quick multilingual"
        },
        "base": {
            "filename": "ggml-base.bin",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
            "size_mb": 142,
            "ram_mb": 500,
            "language": "multilingual",
            "speed": "fast",
            "accuracy": "good",
            "recommended_for": "balanced speed/accuracy, Hindi"
        },
        "small": {
            "filename": "ggml-small.bin",
            "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
            "size_mb": 466,
            "ram_mb": 1000,
            "language": "multilingual",
            "speed": "medium",
            "accuracy": "better",
            "recommended_for": "better accuracy, 8GB+ RAM"
        }
    }
    
    # Default model for different scenarios
    DEFAULT_MODEL = "tiny.en"
    DEFAULT_MULTILINGUAL = "tiny"
    
    # ================================================================
    # MODEL HELPER METHODS
    # ================================================================
    
    @classmethod
    def get_model_path(cls, model_name: str) -> Path:
        """Get full path to model file."""
        if model_name not in cls.MODELS:
            available = list(cls.MODELS.keys())
            raise ValueError(f"Unknown model: '{model_name}'. Available: {available}")
        return cls.MODELS_DIR / cls.MODELS[model_name]["filename"]
    
    @classmethod
    def get_model_url(cls, model_name: str) -> str:
        """Get download URL for model."""
        if model_name not in cls.MODELS:
            raise ValueError(f"Unknown model: '{model_name}'")
        return cls.MODELS[model_name]["url"]
    
    @classmethod
    def get_model_info(cls, model_name: str) -> dict:
        """Get complete model information."""
        if model_name not in cls.MODELS:
            raise ValueError(f"Unknown model: '{model_name}'")
        
        info = cls.MODELS[model_name].copy()
        info["name"] = model_name
        info["path"] = str(cls.get_model_path(model_name))
        info["exists"] = cls.get_model_path(model_name).exists()
        return info
    
    @classmethod
    def list_all_models(cls) -> list:
        """List all configured models."""
        return list(cls.MODELS.keys())
    
    @classmethod
    def list_downloaded_models(cls) -> list:
        """List models that are downloaded."""
        downloaded = []
        for name in cls.MODELS:
            if cls.get_model_path(name).exists():
                downloaded.append(name)
        return downloaded
    
    @classmethod
    def is_model_downloaded(cls, model_name: str) -> bool:
        """Check if model file exists."""
        try:
            return cls.get_model_path(model_name).exists()
        except ValueError:
            return False
    
    @classmethod
    def get_whisper_binary(cls) -> Path:
        """Get path to whisper.cpp executable."""
        if not cls.WHISPER_BINARY.exists():
            raise FileNotFoundError(
                f"Whisper binary not found at: {cls.WHISPER_BINARY}\n"
                "Please build whisper.cpp first. See: engine/BUILD.md"
            )
        return cls.WHISPER_BINARY
    
    @classmethod
    def verify_setup(cls) -> dict:
        """Verify engine setup status."""
        return {
            "engine_dir": str(cls.ENGINE_DIR),
            "models_dir": str(cls.MODELS_DIR),
            "models_dir_exists": cls.MODELS_DIR.exists(),
            "whisper_binary": str(cls.WHISPER_BINARY),
            "whisper_binary_exists": cls.WHISPER_BINARY.exists(),
            "downloaded_models": cls.list_downloaded_models(),
            "total_models_available": len(cls.MODELS)
        }


# ================================================================
# STANDALONE EXECUTION
# ================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("SPEECHEE ENGINE CONFIGURATION")
    print("=" * 65)
    
    # Directory info
    print(f"\n[DIRECTORIES]")
    print(f"  Engine:  {EngineConfig.ENGINE_DIR}")
    print(f"  Models:  {EngineConfig.MODELS_DIR}")
    print(f"  Binary:  {EngineConfig.WHISPER_BINARY}")
    
    # Binary status
    binary_status = "✓ Found" if EngineConfig.WHISPER_BINARY.exists() else "✗ Not Found"
    print(f"\n[WHISPER.CPP STATUS]: {binary_status}")
    
    # Model info
    print(f"\n[MODELS]")
    print("-" * 65)
    print(f"{'Name':<10} {'Size':<8} {'RAM':<8} {'Language':<15} {'Status':<12}")
    print("-" * 65)
    
    for model_name in EngineConfig.list_all_models():
        info = EngineConfig.get_model_info(model_name)
        status = "✓ Ready" if info["exists"] else "✗ Missing"
        print(f"{model_name:<10} {info['size_mb']:<8} {info['ram_mb']:<8} {info['language']:<15} {status:<12}")
    
    print("-" * 65)
    downloaded = EngineConfig.list_downloaded_models()
    print(f"\nDownloaded: {len(downloaded)}/{len(EngineConfig.MODELS)} models")
    print(f"Default Model: {EngineConfig.DEFAULT_MODEL}")
    print("=" * 65)