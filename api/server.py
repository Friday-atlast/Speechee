"""
Speechee API - Server
FastAPI application entry point.
"""

import sys
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .routes import router

# ================================================================
# LOGGING
# ================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("speechee.api")

# ================================================================
# STARTUP TIME TRACKING
# ================================================================

_startup_time = None


def get_uptime() -> float:
    """Get server uptime in seconds."""
    if _startup_time:
        return time.time() - _startup_time
    return 0.0


# ================================================================
# LIFESPAN
# ================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _startup_time
    _startup_time = time.time()
    
    logger.info("=" * 50)
    logger.info("🚀 Speechee API Starting...")
    
    # Check engine
    try:
        from engine import EngineConfig
        if EngineConfig.WHISPER_BINARY.exists():
            logger.info("✓ Whisper engine: Ready")
        else:
            logger.warning("⚠ Whisper engine: Not found")
        
        models = EngineConfig.list_downloaded_models()
        logger.info(f"✓ Models available: {len(models)} ({', '.join(models) if models else 'none'})")
    except Exception as e:
        logger.warning(f"⚠ Engine check failed: {e}")
    
    logger.info("✓ Speechee API Ready!")
    logger.info("=" * 50)
    
    yield
    
    logger.info("👋 Speechee API Shutting down...")


# ================================================================
# APP CREATION
# ================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Speechee API",
        description="""
## Speechee — Offline-First Speech-to-Text API

### Features
- 🎙️ Audio file transcription
- 🔴 Live microphone recording  
- 🌍 Multi-language support (English, Hindi, Hinglish)
- 💾 Fully offline processing
- ⚡ Optimized for low-end devices

### Quick Start
1. Check health: `GET /health`
2. Transcribe file: `POST /stt` with audio file
3. List models: `GET /models`
        """,
        version="1.0.0-dev",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        
        # Skip logging for static files and docs
        if not request.url.path.startswith(("/static", "/docs", "/redoc", "/openapi")):
            logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.3f}s)")
        
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        return response
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc)}
        )
    
    # Include routes
    app.include_router(router)
    
    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # UI endpoint
    @app.get("/ui", include_in_schema=False)
    async def serve_ui():
        html_path = static_dir / "index.html"
        if html_path.exists():
            return FileResponse(html_path)
        return {"message": "UI not available. Visit /docs for API documentation."}
    
    return app


# Create app instance
app = create_app()


# ================================================================
# RUN SERVER
# ================================================================

def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False
):
    """Run the API server."""
    import uvicorn
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║               🎙️  SPEECHEE API SERVER                     ║
╠══════════════════════════════════════════════════════════╣
║  URL:      http://{host}:{port}                         ║
║  Docs:     http://{host}:{port}/docs                    ║
║  Health:   http://{host}:{port}/health                  ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Speechee API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, reload=args.reload)