# `stt/` — Speech-to-Text Core

## Purpose

The `stt/` package is Speechee’s core transcription layer.

It provides:

- Offline transcription via a local `whisper.cpp` binary (`whisper-cli.exe`)
- Live microphone workflows built on top of the audio subsystem
- Output formatting and transcript file management
- Language detection utilities and model recommendations

## Key modules

- `offline.py`
  - `OfflineTranscriber`: validates inputs, builds whisper.cpp CLI arguments, runs transcription via `subprocess`, parses output, and returns a structured result.
- `live_stt.py`
  - `LiveSTT`: records microphone audio, transcribes it, and manages temp file cleanup.
- `formatter.py`
  - `OutputFormatter`: formats transcripts into `txt`, `json`, `srt`, and `vtt`.
- `output_manager.py`
  - `OutputManager`: saves/loads/lists/deletes transcript files under `output/transcripts/`.
- `language.py`
  - `LanguageManager`: language detection (including Hinglish heuristics), model recommendation, and language validation helpers.
- `exceptions.py`
  - Custom exception types raised by the STT layer.

## High-level architecture

```text
Audio file -> OfflineTranscriber
  -> builds whisper command
  -> runs whisper-cli.exe
  -> reads output file
  -> returns result

Mic input -> AudioRecorder -> WAV -> OfflineTranscriber
```

## Public APIs

Typical imports:

- `from stt import OfflineTranscriber`
- `from stt import LiveSTT`
- `from stt import OutputFormatter`
- `from stt import OutputManager`
- `from stt import LanguageManager`

## Configuration

Primary keys consumed by STT:

- `stt.model`
- `stt.language`
- `stt.threads`
- `stt.translate`
- `output.format`
- `output.transcripts_dir`
- `output.temp_dir`

## Examples

### Transcribe a file

```python
from stt import OfflineTranscriber

transcriber = OfflineTranscriber(model="tiny.en", language="en")
result = transcriber.transcribe("tests/test_audio/jfk.wav")
print(result.text)
```

### Live microphone transcription

```python
from stt import LiveSTT

live = LiveSTT(model="tiny", language="auto")
result = live.listen(duration=5)
print(result.text)
```

### Save a transcript

```python
from stt import OutputManager

manager = OutputManager()
saved = manager.save("hello", format="txt", model="tiny.en", language="en")
print(saved.filepath)
```

## How this connects to other folders

- `engine/`: provides binary and model locations used by `OfflineTranscriber`
- `audio/`: provides recording and preprocessing used by `LiveSTT`
- `config/`: supplies merged defaults/overrides
- `output/`: stores temp audio and saved transcripts
- `api/` and `cli/`: are the primary consumers of the STT API

## Related documentation

- Usage: `docs/USAGE.md`
- CLI: `docs/CLI.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
