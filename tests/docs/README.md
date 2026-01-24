# `tests/` — Test Scripts and Fixtures

## Purpose

The `tests/` folder contains lightweight test scripts and fixtures for validating:

- The FastAPI endpoints
- Language detection behavior

This repository uses **script-style tests** (not a full pytest suite).

## Contents

- `test_api.py`
  - Exercises API endpoints and prints a pass/fail summary
- `test_language.py`
  - Exercises `LanguageManager` detection and recommendation logic
- `test_audio/`
  - Audio fixtures used by tests and benchmarks

## Running tests

### API tests

The API tests require the server to be running.

1. Start the server:

```powershell
python api\server.py
```

2. Run:

```powershell
python tests\test_api.py
```

### Language tests

```powershell
python tests\test_language.py
```

## How this connects to other folders

- `api/`: tests API endpoints
- `stt/`: tests language detection logic
- `tools/`: benchmarks use the same `tests/test_audio/` fixtures

## Related documentation

- API docs: `docs/API.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
