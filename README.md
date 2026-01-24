# Speechee — Offline-First Speech-to-Text

## Overview
Offline-first Speech-to-Text engine designed for low-end devices (i3, 4GB RAM, Raspberry Pi).

## Version
- Current: v1.0.0-dev (Development)
- Status: In Progress

## Scope Lock (v1.0.0)
### Included
- Offline STT using whisper.cpp
- CLI tool
- REST API (FastAPI)
- Basic Web UI
- Multi-language support (English, Hindi, Hinglish)
- File transcription (WAV, MP3, M4A)
- Microphone input

### Excluded (Future Versions)
- TTS (Text-to-Speech)
- Wake word detection
- Streaming STT
- Mobile apps
- Cloud deployment

## Target Devices
- Intel i3 or equivalent
- 4GB RAM minimum
- No GPU required
- Raspberry Pi 4 compatible

## Tech Stack
| Component | Technology |
|-----------|------------|
| STT Engine | whisper.cpp (C++) |
| Wrapper | Python 3.10+ |
| API | FastAPI |
| Audio | PyAudio, FFmpeg |
| Models | Quantized Whisper (GGML) |

## Directory Structure

stt-system/
├─ engine/ # whisper.cpp + models
├─ audio/ # Audio capture & preprocessing
├─ stt/ # STT wrapper modules
├─ api/ # FastAPI server + Web UI
├─ cli/ # Command line interface
├─ config/ # Configuration files
├─ output/ # Transcription outputs
├─ docs/ # Documentation
└─ tests/ # Test files

## Quick Start

Documentation entry point:

- `docs/README.md`

### 1) Install

Follow:

- `docs/INSTALLATION.md`

### 2) Run the CLI

If installed (recommended):

```powershell
pip install -e .
speechee --help
```

If not installed:

```powershell
python cli\speechee.py --help
```

### 3) Run the API + Web UI

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/ui`

## Development Timeline
- Day 0: Foundation 
- Day 1-3: Whisper.cpp Integration
- Day 4-7: Audio + CLI
- Day 8-11: API + Web UI
- Day 12-14: Testing + Release

## License
MIT License

## Author
Friday