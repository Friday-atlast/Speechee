# Speechee — Engine Build Instructions

## Overview
This document explains how to build the whisper.cpp STT engine for Speechee.

Speechee expects the built binary at:

- `engine/whisper.cpp/build/bin/Release/whisper-cli.exe`

Speechee expects Whisper model files under:

- `engine/models/`

## Prerequisites

### Windows 10/11
- **Git** — [Download](https://git-scm.com/downloads)
- **Visual Studio Community** — [Download](https://visualstudio.microsoft.com/)
  - Workload: "Desktop development with C++"
- **CMake** (if not already included with your Visual Studio install)

## Build Steps

### 1. Open Developer Command Prompt
```
Windows Search → "Developer Command Prompt for VS" (or "Developer PowerShell for VS")
```

### 2. Navigate to Engine Folder
```cmd
cd path\to\speechee\engine
```

### 3. Clone whisper.cpp

If `engine/whisper.cpp/` already exists (vendored with this repo), skip this step.

```cmd
git clone https://github.com/ggerganov/whisper.cpp.git whisper.cpp
cd whisper.cpp
```

### 4. Create Build Directory
```cmd
mkdir build
cd build
```

### 5. Configure CMake
```cmd
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### 6. Build
```cmd
cmake --build . --config Release
```

### 7. Verify Build
```cmd
dir bin\Release\whisper-cli.exe
```

## Download Model

### Tiny Model (Recommended for low-end devices)

Recommended (via Speechee model manager):

```cmd
python model_manager.py download --model tiny.en
```

Manual download (direct URL):

```cmd
cd models
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin' -OutFile 'ggml-tiny.en.bin'"
```

### Manual Download
- URL: https://huggingface.co/ggerganov/whisper.cpp/tree/main
- File: ggml-tiny.en.bin
- Save to: `engine/models/`

## Test Installation

```cmd
cd build
bin\Release\whisper-cli.exe -m ..\..\models\ggml-tiny.en.bin -f ..\samples\jfk.wav
```

### Expected Output
```
[00:00:00.000 --> 00:00:11.000]   And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country.
```

## Available Models

| Model | Size | RAM Usage | Speed | Accuracy |
|-------|------|-----------|-------|----------|
| tiny.en | ~75 MB | ~400 MB | Fastest | Basic |
| tiny | ~75 MB | ~500 MB | Fast | Better multilingual |
| base | ~142 MB | ~800 MB | Medium | Good |
| small | ~466 MB | ~1.5 GB | Slow | Better |

**Recommendation:** Use `tiny.en` for English-only development on low-end devices; use `base` when you need better quality (and can afford the extra CPU/RAM).

## Troubleshooting

### Error: "cmake is not recognized"
- Install CMake or enable it in your Visual Studio installer
- Use Developer Command Prompt/PowerShell, not a regular shell

### Error: "cl is not recognized"
- Visual Studio C++ workload is not installed ("Desktop development with C++")
- Make sure you are using a Developer Command Prompt/PowerShell

### Error: Build fails with missing header
- Delete build folder
- Re-run cmake and build commands

### Error: Model file corrupted
- Verify file size (example: tiny.en is commonly `77,691,713` bytes)
- Re-download if the size is different or the download was interrupted
