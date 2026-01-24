# Use Cases and Capabilities

## What this project does

Speechee converts speech audio into text **offline**, using a local whisper.cpp engine.

## Why it exists

- To run STT on low-end devices
- To avoid cloud dependencies and data leakage
- To provide a simple CLI + API for local automation

## Who should use it

- Developers who want offline STT
- Hobby projects (assistants, automation)
- Tools that need basic multilingual STT (including Hindi / Hinglish)

## Capabilities

- Audio file transcription (`.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`)
- Microphone recording + transcription (local machine)
- FastAPI server providing STT and utility endpoints
- Basic web UI
- Model downloading and verification
- Output formatting (txt/json/srt/vtt)
- Language detection and model recommendations
- Performance monitoring (CPU/RAM)

## Example workflows

## Workflow A: Transcribe a meeting recording

1. Download a multilingual model:

```powershell
speechee models recommended
```

2. Transcribe the file:

```powershell
speechee transcribe meeting.mp3 -m base -l auto --save
```

3. Find the output under:

- `output/transcripts/`

## Workflow B: Hindi transcription

```powershell
speechee transcribe Hindi.wav -m tiny -l hi --save
```

## Workflow C: Local API integration

1. Run server:

```powershell
speechee api
```

2. POST a file to `/stt`.

## Workflow D: Benchmark models on your device

```powershell
python tools\benchmark.py full --audio tests\test_audio\jfk.wav
```
