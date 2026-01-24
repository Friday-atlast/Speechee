# `audio/` — Audio Capture and Preprocessing

## Purpose

The `audio/` package contains utilities for:

- Microphone enumeration and selection
- Recording from the microphone to WAV
- Audio inspection and preprocessing to be compatible with whisper.cpp

## Key modules

- `mic.py`
  - `Microphone`: lists input devices, chooses a device, and can run basic microphone tests.
- `recorder.py`
  - `AudioRecorder`: records from the microphone using either `sounddevice` or `pyaudio`.
  - Saves recordings as WAV (commonly under `output/temp/`).
- `preprocess.py`
  - `AudioPreprocessor`: reads audio metadata, checks whisper compatibility, and provides conversion/normalization helpers.

## Typical workflows

### Device enumeration

```text
Microphone.list_devices() -> used by CLI (devices) and API (/devices)
```

### Record + transcribe

```text
AudioRecorder.record_to_file() -> WAV -> stt.OfflineTranscriber.transcribe()
```

## Public APIs

Typical imports:

- `from audio import Microphone`
- `from audio import AudioRecorder`
- `from audio import AudioPreprocessor`

## Configuration

Audio-related keys:

- `audio.sample_rate` (default 16000)
- `audio.channels` (default 1)
- `audio.default_duration`
- `audio.max_duration`
- `audio.device_id`

## Examples

### List devices

```python
from audio import Microphone

mic = Microphone()
devices = mic.list_devices()
print(devices)
```

### Record a WAV

```python
from audio import AudioRecorder

rec = AudioRecorder()
path = rec.record_to_file(duration=5)
print(path)
```

## How this connects to other folders

- `stt/`: consumes recorded audio for live transcription
- `api/`: uses device listing and server-side recording
- `cli/`: exposes `record` and `devices` commands
- `config/`: provides sample rate, channel count, duration defaults

## Related documentation

- Usage: `docs/USAGE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
