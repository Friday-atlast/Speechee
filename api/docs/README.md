# `api/` — FastAPI Server + Web UI

## Purpose

The `api/` package exposes Speechee functionality over HTTP using **FastAPI**.

It provides:

- REST endpoints for transcription, health/status, model listing, device listing, config inspection, language detection, and transcript management
- A lightweight static Web UI served from the same server

## What lives here

- `server.py`
  - Creates and runs the FastAPI application
  - Wires middleware, exception handlers, and router mounting
- `routes.py`
  - The API router and all endpoint implementations
  - Calls into `stt/`, `audio/`, `config/`, and `engine/`
- `static/`
  - `index.html`, CSS, and JS for the browser UI
  - `js/api.js` is the browser-side API client
  - `js/app.js` is the UI controller logic

## High-level architecture

```text
Browser UI (optional)
  -> /stt, /models, /devices, /language/detect, /transcripts ...
      -> stt.OfflineTranscriber / stt.LiveSTT
      -> audio.* for recording and device enumeration
      -> config.Settings for merged config
      -> engine.ModelManager for model inspection
      -> output files under output/ (temp + transcripts)
```

## Public endpoints (summary)

See root docs:

- `docs/API.md`

Key behaviors:

- `POST /stt` uploads an audio file, writes a temp file under `output/temp/`, transcribes via whisper.cpp, then deletes the temp file.
- `/ui` serves the static UI that calls the API endpoints.

## Configuration

Runtime config comes from `config/defaults.json` merged with `config/config.json`.

API-related keys:

- `api.enabled`
- `api.host`
- `api.port`
- `api.cors_origins`

## Examples

### Run API locally

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

### Use the Web UI

- `http://127.0.0.1:8000/ui`

## How this connects to other folders

- `stt/`: primary transcription logic used by `/stt` and `/listen`
- `audio/`: microphone listing/recording for `/devices` and `/listen`
- `engine/`: model metadata + model listing
- `config/`: merged settings exposed via `/config`
- `output/`: temp uploads and saved transcripts

## Common failure modes

- Missing whisper binary (`engine/whisper.cpp/.../whisper-cli.exe`)
- Missing model files (`engine/models/*.bin`)
- Microphone device access issues on the server host (for `/listen`)

## Related documentation

- Root API docs: `docs/API.md`
- Usage: `docs/USAGE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
