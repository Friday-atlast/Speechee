# Installation Guide

This guide installs Speechee for **local/offline** use on Windows.

## What you are installing

Speechee consists of:

- **Python packages** (CLI, API, audio utilities)
- A native **whisper.cpp** binary (`whisper-cli.exe`) that runs transcription
- One or more **Whisper model files** (`ggml-*.bin`)

> Speechee does **not** require a GPU.

## Platform / device requirements

- **OS**: Windows 10/11
- **Python**: 3.9+ (recommended 3.10+)
- **CPU/RAM**:
  - Minimum: Intel i3 / 4 GB RAM (project target)
  - Recommended: 8 GB RAM for larger models
- **Disk**:
  - Python deps: ~200–500 MB (depends on your environment)
  - Models: ~75 MB (tiny) up to ~466 MB (small)

## 1) Get the source code

Clone or download this repository.

## 2) Create and activate a virtual environment

From the repo root:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

## 3) Install Python dependencies

```powershell
pip install -r requirements.txt
```

Optional (editable install to expose the `speechee` command):

```powershell
pip install -e .
```

## 4) Install audio backend (Windows)

Speechee can record using either:

- `sounddevice` (preferred)
- `pyaudio`

This repository includes both in `requirements.txt`, but on Windows `pyaudio` sometimes fails to install without a wheel.

If you have issues:

- Prefer using the `sounddevice` backend (already included)
- If you must use `pyaudio`, install a compatible wheel (or use your preferred Windows Python wheel source)

## 5) Build whisper.cpp (engine)

The transcription engine is **not** a Python library. You must build `whisper-cli.exe`.

Follow:

- `engine/BUILD.md`

Expected output binary path used by Speechee:

- `engine/whisper.cpp/build/bin/Release/whisper-cli.exe`

## 6) Download Whisper models

Models are downloaded to:

- `engine/models/`

You can download via:

```powershell
python engine\model_manager.py recommended
```

Or download an individual model:

```powershell
python engine\model_manager.py download --model tiny
```

Available model names in this project:

- `tiny.en`
- `tiny`
- `base`
- `small`

## 7) Verify installation

### CLI check

```powershell
speechee info
```

If you did not install editable mode, you can run:

```powershell
python cli\speechee.py info
```

### API check

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs` (Swagger)
- `http://127.0.0.1:8000/ui` (Web UI)

## Common installation problems

See `docs/TROUBLESHOOTING.md`.
