# Troubleshooting

## 1) “Whisper binary not found”

Symptoms:

- CLI/API fails with an error about `whisper-cli.exe` not existing.

Cause:

- `engine/whisper.cpp` has not been built.

Fix:

- Follow `engine/BUILD.md`
- Confirm the binary exists at:
  - `engine/whisper.cpp/build/bin/Release/whisper-cli.exe`

## 2) “Model not found”

Cause:

- The model file is missing under `engine/models/`.

Fix:

```powershell
python engine\model_manager.py recommended
```

Or a single model:

```powershell
python engine\model_manager.py download --model tiny
```

## 3) Audio recording fails (no backend)

Cause:

- Neither `sounddevice` nor `pyaudio` is installed/working.

Fix:

- Prefer `sounddevice` on Windows:

```powershell
pip install sounddevice soundfile
```

## 4) Microphone not detected

Try:

```powershell
speechee devices
```

If no devices are listed:

- Check Windows privacy settings for microphone access
- Ensure an input device is enabled in Windows sound settings

## 5) API is running but UI shows Offline

Causes:

- API is not reachable at the same origin the browser is using
- CORS / network mismatch

Fix:

- Use `http://127.0.0.1:8000/ui`
- Check `http://127.0.0.1:8000/health`

## 6) API transcription returns success=false

Common causes:

- Unsupported file extension
- Whisper binary missing
- Model missing

Fix:

- Confirm file extension is one of: wav, mp3, m4a, flac, ogg, webm
- Run `speechee info` to check engine and models

## 7) Hindi audio outputs English

This happens when **translation** is enabled.

Fix:

- Use multilingual model (`tiny`, `base`)
- Ensure translation is disabled:
  - API: `translate=false`
  - Python: `OfflineTranscriber(..., translate=False)`

## 8) Performance problems / high RAM usage

- Use a smaller model (`tiny.en` or `tiny`)
- Lower CPU threads in config:

```powershell
speechee config set stt.threads 2
```

Use the monitoring tools:

```powershell
python tools\benchmark.py quick
python tools\monitor.py system
```
