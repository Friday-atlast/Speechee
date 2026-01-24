# API Documentation (FastAPI)

Speechee exposes a local REST API implemented with **FastAPI**.

- Entry point: `api/server.py`
- Routes: `api/routes.py`
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Running the server

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

Or:

```powershell
speechee api --host 127.0.0.1 --port 8000
```

## Response conventions

Most endpoints return JSON objects.

Transcription endpoints generally include:

- `success`: boolean
- `text`: transcript
- `error`: error string when `success=false`

## Endpoints

## `GET /`

System metadata.

Returns:

- API name/version
- A list of important endpoints

## `GET /health`

Health check.

Returns:

- `status`: `healthy` / `degraded` / `error`
- `engine_ready`: whether `whisper-cli.exe` exists
- `models_available`: number of downloaded models
- `models_list`: model names

## `POST /stt`

Transcribe an uploaded audio file.

Consumes:

- `multipart/form-data`

Form fields:

- `file` (required): audio file
- `model` (optional, default `tiny`): model name
- `language` (optional, default `auto`): ISO language code (e.g. `en`, `hi`) or `auto`
- `translate` (optional, default `false`): translate to English

Behavior:

- Saves the upload under `output/temp/`
- Runs `stt.OfflineTranscriber(...).transcribe(...)`
- Deletes the temp file in a `finally` block

Example (curl):

```bash
curl -X POST http://127.0.0.1:8000/stt \
  -F "file=@tests/test_audio/jfk.wav" \
  -F "model=tiny.en" \
  -F "language=en" \
  -F "translate=false"
```

## `POST /listen`

Record audio on the server machine (microphone attached to server) and transcribe.

Consumes:

- JSON body (`ListenRequest`):
  - `duration` (1–300)
  - `model`
  - `language`

Returns:

- `text`
- `duration_sec`
- `latency_sec`

> Note: This endpoint requires microphone access on the server host.

## `GET /models`

List available models and whether they are downloaded.

Returns:

- `total`, `downloaded`, `default`, `models[]`

Each model item includes:

- `name`
- `downloaded`
- `size_mb`, `ram_mb`, `language`, `speed`

## `GET /config`

Returns the merged runtime configuration and the path to `config/config.json`.

## `GET /devices`

List audio input devices.

Returns:

- `total`
- `default_index`
- `devices[]`

## `GET /language/detect`

Query parameter:

- `text`: required

Returns:

- detected language code/name/confidence
- whether Hinglish was detected
- recommended model

## `GET /transcripts`

Query parameter:

- `limit` (1–100)

Returns:

- list of saved transcripts from `output/transcripts/`
- storage stats

## `GET /transcripts/{filename}`

Returns the content of one saved transcript.

## `DELETE /transcripts/{filename}`

Deletes a transcript file.

## Web UI

- `GET /ui` serves `api/static/index.html` (if present)
- Static assets are mounted at `/static`, `/css`, `/js`

## Error handling

- Invalid upload type returns `400`
- Unknown transcript returns `404`
- Unhandled server exceptions return `500` with `{ "success": false, "error": "..." }`
