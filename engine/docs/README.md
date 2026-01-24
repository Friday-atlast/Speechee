# `engine/` — whisper.cpp Integration + Model Management

## Purpose

The `engine/` folder contains everything needed to run whisper.cpp locally:

- A vendored copy of `whisper.cpp`
- Build instructions for producing `whisper-cli.exe`
- Model metadata and model download/verification utilities

## Key files

- `BUILD.md`
  - Step-by-step build instructions for Windows
- `config.py`
  - `EngineConfig`: authoritative paths and model metadata used by the rest of Speechee
- `model_manager.py`
  - `ModelManager`: download, verify, list, and manage models in `engine/models/`
- `models/`
  - Model storage directory (GGML `.bin` files)
- `whisper.cpp/`
  - Upstream repository (C/C++ code)

## Build output

Expected binary path used by Speechee:

- `engine/whisper.cpp/build/bin/Release/whisper-cli.exe`

## Model management

Models are stored under:

- `engine/models/`

Common workflows:

```powershell
python engine\model_manager.py list
python engine\model_manager.py recommended
python engine\model_manager.py verify
```

## How this connects to other folders

- `stt/`: executes the built `whisper-cli.exe` and selects model files
- `api/` and `cli/`: expose model listing and download/verify commands
- `config/`: provides the models directory path and default model selection

## Related documentation

- Engine build: `engine/BUILD.md`
- Installation: `docs/INSTALLATION.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
