# Usage (How to Run Speechee)

This guide shows how to use Speechee via:

- CLI (`speechee`)
- REST API (FastAPI)
- Web UI (`/ui`)

## Quick mental model

Speechee runs transcription by executing **whisper.cpp** (`whisper-cli.exe`) with a chosen model file.

Data flow (file transcription):

```text
Audio file -> OfflineTranscriber -> whisper-cli.exe -> output text file -> returned to caller
```

Data flow (microphone transcription):

```text
Microphone -> AudioRecorder -> temp WAV -> OfflineTranscriber -> whisper-cli.exe -> text
```

## 1) CLI

### Show help

```powershell
speechee --help
```

### Live microphone transcription

```powershell
speechee listen
```

Common options:

- `-d/--duration`: seconds
- `-m/--model`: model name (e.g. `tiny.en`, `tiny`, `base`)
- `-l/--language`: `auto`, `en`, `hi`, ...
- `--save`: save transcript to `output/transcripts/`

Example (Hindi transcription, do not translate):

```powershell
speechee listen -m tiny -l hi
```

### Transcribe an audio file

```powershell
speechee transcribe path\to\audio.wav
```

Example:

```powershell
speechee transcribe tests\test_audio\jfk.wav -m tiny.en -l en --save
```

### Record audio only (no transcription)

```powershell
speechee record -d 10 -o sample.wav
```

### Model management

```powershell
speechee models list
speechee models recommended
speechee models download base
speechee models verify
```

### Configuration

```powershell
speechee config show
speechee config get stt.model
speechee config set stt.model base
```

### Saved transcripts

```powershell
speechee outputs list
speechee outputs stats
speechee outputs clear --confirm
```

## 2) API (FastAPI)

### Run the API server

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

Or via CLI:

```powershell
speechee api --host 127.0.0.1 --port 8000
```

### Useful URLs

- `GET /health`: engine status
- `GET /docs`: Swagger UI
- `GET /redoc`: ReDoc
- `GET /ui`: Web UI

## 3) Web UI

The UI is served by the API server.

1. Start the API.
2. Open: `http://127.0.0.1:8000/ui`

UI features:

- Upload audio and transcribe
- Record in the browser (uses browser microphone) and transcribe
- Language detection demo
- View/delete saved transcripts

> Note: Browser recording is processed by the browser and then uploaded to `POST /stt`.

## Output locations

- **Temporary audio**: `output/temp/`
- **Saved transcripts**: `output/transcripts/`

## Supported audio formats

Speechee accepts:

- `.wav`
- `.mp3`
- `.m4a`
- `.flac`
- `.ogg`
- `.webm`

## Language behavior: transcribe vs translate

- Default behavior is **transcribe** (keep the original language)
- API supports an explicit `translate` flag

For Hindi audio output as Hindi text:

- Use a multilingual model (e.g. `tiny`, `base`)
- Set `language=hi`
- Set `translate=false`
