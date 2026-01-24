# Architecture

This document explains how Speechee works internally.

## High-level goals

- Run **Speech-to-Text fully offline**
- Be usable on **low-end devices**
- Provide both:
  - A **CLI** for local workflows
  - A **REST API + Web UI** for integration

## Core components

## 1) whisper.cpp engine (`engine/`)

- `engine/whisper.cpp/` is a vendored upstream repository.
- The binary used by Speechee is:
  - `engine/whisper.cpp/build/bin/Release/whisper-cli.exe`

Speechee calls this binary using `subprocess`.

## 2) Model management (`engine/config.py`, `engine/model_manager.py`)

- `EngineConfig` defines:
  - Known model names
  - Download URLs
  - Expected sizes (for basic integrity checks)
  - Paths to the binary and model directory

- `ModelManager` provides:
  - Downloading models with progress
  - Verifying models by size
  - Download presets (essential/recommended/all)

## 3) Speech-to-Text wrapper (`stt/`)

### `OfflineTranscriber`

- Validates:
  - Whisper binary exists
  - Model exists
  - Audio file exists and has a supported extension

- Builds the whisper.cpp command:
  - Uses `-m <model>` and `-f <audio>`
  - Uses `-t <threads>`
  - Adds `-l <language>` when language is not `auto`
  - Adds `--translate` only if requested

- Executes the process and reads the generated output file.

### `LiveSTT`

Pipeline:

1. Record WAV using `audio.AudioRecorder`
2. Transcribe with `OfflineTranscriber`
3. Cleanup temp audio (unless `keep_audio`)

### `LanguageManager`

- Uses `langdetect` if installed
- Implements a fallback heuristic (script checks)
- Adds Hinglish heuristics (mixed Devanagari/Latin)
- Provides model recommendations

### Output handling

- `OutputFormatter` can format:
  - `txt`
  - `json`
  - `srt`
  - `vtt`

- `OutputManager` saves outputs in `output/transcripts/` and can list/delete files.

## 4) Audio subsystem (`audio/`)

- `Microphone`: enumerates devices and tests input
- `AudioRecorder`: records to WAV using either `sounddevice` or `pyaudio`
- `AudioPreprocessor`: inspects and transforms audio (normalize / resample / mono)

## 5) API layer (`api/`)

- FastAPI server in `api/server.py`
- All endpoints in `api/routes.py`
- Uses the same `stt` and `audio` modules as the CLI

## 6) Web UI (`api/static/`)

- Served from `/ui`
- Uses a small JS client (`api/static/js/api.js`) to call the REST endpoints

## Configuration (`config/`)

Configuration sources:

1. `config/defaults.json` (base defaults)
2. `config/config.json` (user overrides)
3. Runtime overrides (via `Settings.set()`)

`Settings` merges configs with a deep merge and exposes dot-notation access.

## Repository layout

```text
Speechee/
  api/        FastAPI server + static Web UI
  audio/      microphone capture + preprocessing
  cli/        CLI entrypoint
  config/     config files and Settings manager
  engine/     whisper.cpp integration + models
  output/     runtime output directory (temp + transcripts)
  stt/        transcription wrapper modules
  tools/      benchmarking and monitoring
  tests/      lightweight test scripts and fixtures
```
