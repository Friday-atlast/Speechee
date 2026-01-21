# Speechee — Engine Build Instructions

## Overview
This document explains how to build the whisper.cpp STT engine for Speechee.

## Prerequisites

### Windows 10/11
- **Git** — [Download](https://git-scm.com/downloads)
- **Visual Studio 2026 Community** — [Download](https://visualstudio.microsoft.com/)
  - Workload: "Desktop development with C++"

## Build Steps

### 1. Open Developer Command Prompt
```
Windows Search → "Developer Command Prompt for VS 2022"
```

### 2. Navigate to Engine Folder
```cmd
cd path\to\speechee\engine
```

### 3. Clone whisper.cpp
```cmd
git clone https://github.com/ggerganov/whisper.cpp.git
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
dir bin\Release\main.exe
```

## Download Model

### Tiny Model (Recommended for low-end devices)
```cmd
cd ..\models
powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin' -OutFile 'ggml-tiny.en.bin'"
```

### Manual Download
- URL: https://huggingface.co/ggerganov/whisper.cpp/tree/main
- File: ggml-tiny.en.bin
- Save to: `engine/whisper.cpp/models/`

## Test Installation

```cmd
cd build
bin\Release\main.exe -m ..\models\ggml-tiny.en.bin -f ..\samples\jfk.wav
```

### Expected Output
```
[00:00:00.000 --> 00:00:11.000]   And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country.
```

## Available Models

| Model | Size | RAM Usage | Speed | Accuracy |
|-------|------|-----------|-------|----------|
| tiny.en | 75 MB | ~400 MB | Fastest | Basic |
| base.en | 142 MB | ~800 MB | Fast | Good |
| small.en | 466 MB | ~1.5 GB | Medium | Better |
| medium.en | 1.5 GB | ~3 GB | Slow | Best |

**Recommendation:** Use `tiny.en` for development, `base.en` for production on low-end devices.

## Troubleshooting

### Error: "cmake is not recognized"
- Use Developer Command Prompt, not regular CMD

### Error: "cl is not recognized"
- Visual Studio C++ workload not installed
- Reinstall VS with "Desktop development with C++"

### Error: Build fails with missing header
- Delete build folder
- Re-run cmake and build commands

### Error: Model file corrupted
- Verify file size (tiny.en = 77,691,713 bytes)
- Re-download if size is different
