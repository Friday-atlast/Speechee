# `tools/` — Benchmarking and Monitoring

## Purpose

The `tools/` folder contains utilities for evaluating Speechee performance on real hardware.

These tools are intended for:

- CPU/RAM usage measurement during transcription
- Comparing models by runtime and resource consumption

## Key modules

- `monitor.py`
  - `ResourceMonitor`: captures CPU and RAM snapshots and can monitor a transcription run
- `benchmark.py`
  - Benchmarks multiple models against a given audio file and reports timing/resource summaries

## Examples

### System info / current usage

```powershell
python tools\monitor.py system
python tools\monitor.py current
```

### Monitor a transcription

```powershell
python tools\monitor.py transcribe --audio tests\test_audio\jfk.wav --model tiny.en
```

### Benchmark models

```powershell
python tools\benchmark.py quick --audio tests\test_audio\jfk.wav
python tools\benchmark.py full --audio tests\test_audio\jfk.wav
```

## How this connects to other folders

- `stt/`: benchmark/monitor calls into `OfflineTranscriber`
- `engine/`: tools rely on models and the whisper binary
- `tests/`: uses audio fixtures under `tests/test_audio/`

## Related documentation

- Usage: `docs/USAGE.md`
- Platform requirements: `docs/PLATFORM_REQUIREMENTS.md`
