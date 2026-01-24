"""
Speechee API - Routes
All REST API endpoints.
"""

import os
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ================================================================
# PYDANTIC MODELS
# ================================================================

class STTResponse(BaseModel):
    """Response model for /stt endpoint."""
    success: bool
    text: str = ""
    language: Optional[str] = None
    model: str = ""
    duration_sec: Optional[float] = None
    processing_time_sec: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    version: str
    engine_ready: bool
    models_available: int
    models_list: list
    timestamp: str


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    downloaded: bool
    size_mb: int
    language: str


class ModelsResponse(BaseModel):
    """Response for /models endpoint."""
    total: int
    downloaded: int
    default: str
    models: list


class ListenRequest(BaseModel):
    """Request for /listen endpoint."""
    duration: float = Field(default=5.0, ge=1.0, le=300.0)
    model: str = "tiny.en"
    language: str = "auto"


class ListenResponse(BaseModel):
    """Response for /listen endpoint."""
    success: bool
    text: str = ""
    duration_sec: float = 0.0
    latency_sec: float = 0.0
    model: str = ""
    error: Optional[str] = None


# ================================================================
# ROUTER
# ================================================================

router = APIRouter()

# Allowed audio extensions
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


# ================================================================
# ENDPOINTS
# ================================================================

@router.get("/", tags=["System"])
async def root():
    """API root - welcome message."""
    return {
        "name": "Speechee API",
        "version": "1.0.0-dev",
        "description": "Offline-First Speech-to-Text REST API",
        "endpoints": {
            "transcribe": "POST /stt",
            "health": "GET /health",
            "models": "GET /models",
            "docs": "GET /docs"
        }
    }


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API and engine health."""
    try:
        from engine import EngineConfig
        
        engine_ready = EngineConfig.WHISPER_BINARY.exists()
        downloaded = EngineConfig.list_downloaded_models()
        
        return HealthResponse(
            status="healthy" if engine_ready else "degraded",
            version="1.0.0-dev",
            engine_ready=engine_ready,
            models_available=len(downloaded),
            models_list=downloaded,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            version="1.0.0-dev",
            engine_ready=False,
            models_available=0,
            models_list=[],
            timestamp=datetime.now().isoformat()
        )


@router.post("/stt", response_model=STTResponse, tags=["Transcription"])
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: str = Form(default="tiny.en", description="Whisper model name"),
    language: str = Form(default="auto", description="Language code or 'auto'")
):
    """
    Transcribe uploaded audio file to text.
    
    - **file**: Audio file (WAV, MP3, M4A, FLAC, OGG, WEBM)
    - **model**: Whisper model (tiny.en, tiny, base, small)
    - **language**: Language code (en, hi, auto)
    
    Returns JSON with transcribed text.
    """
    start_time = time.time()
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Create temp directory
    temp_dir = PROJECT_ROOT / "output" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"upload_{timestamp}_{file.filename}"
    temp_path = temp_dir / temp_filename
    
    try:
        # Write file to disk
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size for duration estimate
        file_size = temp_path.stat().st_size
        
        # Transcribe using existing module
        from stt import OfflineTranscriber
        
        transcriber = OfflineTranscriber(
            model=model,
            language=language,
            verbose=False
        )
        
        result = transcriber.transcribe(str(temp_path), output_format="txt")
        
        processing_time = time.time() - start_time
        
        if result.success:
            return STTResponse(
                success=True,
                text=result.text,
                language=result.language,
                model=model,
                processing_time_sec=round(processing_time, 2),
                error=None
            )
        else:
            return STTResponse(
                success=False,
                text="",
                model=model,
                processing_time_sec=round(processing_time, 2),
                error=result.error
            )
            
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"STT module not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except:
                pass


@router.post("/listen", response_model=ListenResponse, tags=["Transcription"])
async def listen_and_transcribe(request: ListenRequest):
    """
    Record from microphone and transcribe.
    
    - **duration**: Recording duration in seconds (1-300)
    - **model**: Whisper model name
    - **language**: Language code or 'auto'
    
    Note: Requires microphone access on server.
    """
    try:
        from stt import LiveSTT
        
        live = LiveSTT(
            model=request.model,
            language=request.language,
            cleanup=True,
            verbose=False
        )
        
        result = live.listen(duration=request.duration)
        
        return ListenResponse(
            success=result.success,
            text=result.text if result.success else "",
            duration_sec=result.duration_sec,
            latency_sec=result.total_latency_sec,
            model=request.model,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelsResponse, tags=["Models"])
async def list_models():
    """List available Whisper models."""
    try:
        from engine import EngineConfig
        from config import get_settings
        
        settings = get_settings()
        all_models = EngineConfig.list_all_models()
        downloaded = EngineConfig.list_downloaded_models()
        default_model = settings.get("stt.model", "tiny.en")
        
        models = []
        for name in all_models:
            info = EngineConfig.get_model_info(name)
            models.append({
                "name": name,
                "downloaded": info["exists"],
                "size_mb": info["size_mb"],
                "ram_mb": info["ram_mb"],
                "language": info["language"],
                "speed": info["speed"]
            })
        
        return ModelsResponse(
            total=len(all_models),
            downloaded=len(downloaded),
            default=default_model,
            models=models
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", tags=["Config"])
async def get_config():
    """Get current configuration."""
    try:
        from config import Settings
        from config.settings import USER_CONFIG_FILE
        
        settings = Settings()
        return {
            "config": settings.get_all(),
            "config_file": str(USER_CONFIG_FILE)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices", tags=["Audio"])
async def list_audio_devices():
    """List available audio input devices."""
    try:
        from audio import Microphone
        
        mic = Microphone()
        devices = mic.list_devices()
        default = mic.get_default_device()
        
        return {
            "total": len(devices),
            "default_index": default["index"] if default else None,
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/language/detect", tags=["Language"])
async def detect_language(text: str = Query(..., min_length=1, description="Text to analyze")):
    """Detect language of provided text."""
    try:
        from stt import LanguageManager
        
        lm = LanguageManager()
        result = lm.detect(text)
        is_hinglish, mix_ratio = lm.detect_hinglish(text)
        
        return {
            "text": text[:100],
            "detected": {
                "code": result.code,
                "name": result.name,
                "confidence": result.confidence,
                "method": result.method
            },
            "hinglish": {
                "is_hinglish": is_hinglish,
                "mix_ratio": round(mix_ratio, 2)
            },
            "recommended_model": lm.get_recommended_model(result.code)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))