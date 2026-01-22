# Development Roadmap — Speechee v1.0.0

## Timeline: 14 Days

---

## Week 1: Core Engine

### Day 0: Foundation ✅
- [x] Directory structure
- [x] Git repository
- [x] README.md
- [x] Scope lock

### Day 1: Whisper.cpp Build
- [x] Clone whisper.cpp
- [x] CMake build
- [x] Download tiny.en model
- [x] Test CLI transcription

### Day 2: Model Management
- [x] models/ folder setup
- [x] Multiple model support
- [x] Model path configuration

### Day 3: Python Wrapper
- [x] subprocess integration
- [x] Audio file input
- [x] Text output parsing

### Day 4: Microphone Capture
- [x] PyAudio setup
- [x] WAV recording
- [x] 16kHz mono format

### Day 5: Live Integration
- [x] Mic → STT pipeline
- [x] Temp file handling
- [x] Latency testing

### Day 6: Output Formatting
- [x] Plain text output
- [x] JSON output
- [x] Timestamp support

### Day 7: CLI Tool
- [x] argparse setup
- [x] --mic command
- [x] --file command

---

## Week 2: API & Polish

### Day 8: Config System
- [x] config.json structure
- [x] Runtime config loading
- [x] Default fallbacks

### Day 9: Language Support
- [ ] English testing
- [ ] Hindi testing
- [ ] Auto-detection

### Day 10: FastAPI Server
- [ ] API endpoints
- [ ] File upload
- [ ] JSON response

### Day 11: Web UI
- [ ] index.html
- [ ] CSS styling
- [ ] JavaScript logic

### Day 12: Optimization
- [ ] Memory profiling
- [ ] Low-end testing
- [ ] Thread limiting

### Day 13: Documentation
- [ ] Installation guide
- [ ] API documentation
- [ ] Usage examples

### Day 14: Release
- [ ] Final testing
- [ ] v1.0.0 tag
- [ ] GitHub release

---

## Version Tags

| Tag | Description | Branch |
|-----|-------------|--------|
| v1.0.0-dev.1 | Whisper.cpp working | develop |
| v1.0.0-dev.2 | CLI ready | develop |
| v1.0.0-dev.3 | API + Web UI ready | develop |
| v1.0.0 | Stable release | main |

---

## Out of Scope (v1.0.0)
- TTS integration
- Wake word detection
- Mobile app
- Cloud API
- Noise suppression