# Integrations

This document explains how to integrate Speechee with external systems.

## Integration options

- **CLI**: simplest for local scripts (batch processing)
- **REST API**: best for apps/services that need STT
- **Library usage**: import Python modules directly

## 1) Integrate via REST API

### Start the API

```powershell
speechee api --host 127.0.0.1 --port 8000
```

### Upload file transcription

Send a multipart form request to `POST /stt`.

Example (Python):

```python
import requests

with open("tests/test_audio/jfk.wav", "rb") as f:
    r = requests.post(
        "http://127.0.0.1:8000/stt",
        files={"file": ("jfk.wav", f, "audio/wav")},
        data={"model": "tiny.en", "language": "en", "translate": False},
        timeout=120,
    )

print(r.json())
```

### Language detection

Example:

```bash
curl "http://127.0.0.1:8000/language/detect?text=Hello%20world"
```

## 2) Integrate via CLI

Batch process files from another program:

```powershell
speechee transcribe input.wav --save
```

Because the CLI uses exit codes, you can integrate it into scripts and CI.

## 3) Integrate as a Python library

### Offline transcription

```python
from stt import OfflineTranscriber

transcriber = OfflineTranscriber(model="tiny.en", language="en")
result = transcriber.transcribe("tests/test_audio/jfk.wav")
print(result.text)
```

### Live transcription

```python
from stt import LiveSTT

live = LiveSTT(model="tiny", language="hi")
result = live.listen(duration=5)
print(result.text)
```

### Saving output

```python
from stt import OutputManager

manager = OutputManager()
saved = manager.save("hello", format="json", model="tiny.en", language="en")
print(saved.filepath)
```

## Deployment notes

Speechee is designed for **local/offline** usage.

If you run the API in production-like environments:

- Ensure the `engine/whisper.cpp` binary exists on the host
- Ensure model files are present under `engine/models/`
- Consider restricting CORS and limiting upload sizes

## External dependencies

- **whisper.cpp** (vendored under `engine/whisper.cpp`)
- **Model hosting**: HuggingFace URLs in `engine/config.py`
- **Audio input**: system microphone + `sounddevice`/`pyaudio`
