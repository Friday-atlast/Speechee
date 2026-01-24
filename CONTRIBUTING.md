# Contributing to Speechee

Thanks for your interest in contributing to **Speechee**.

This project focuses on **offline-first Speech-to-Text** (STT) using **whisper.cpp** plus a Python CLI and FastAPI server.

## Code of Conduct

By participating, you are expected to uphold the rules in `CODE_OF_CONDUCT.md`.

## Quick links

- Docs entry point: `docs/README.md`
- Installation guide: `docs/INSTALLATION.md`
- Architecture: `docs/ARCHITECTURE.md`
- CLI reference: `docs/CLI.md`
- API reference: `docs/API.md`

## Development setup (Windows)

### Prerequisites

- Windows 10/11
- Python 3.9+ (recommended 3.10+)
- A C/C++ toolchain to build whisper.cpp (see `engine/BUILD.md`)

### 1) Create and activate a virtual environment

From the repo root:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Install Speechee in editable mode (recommended)

This enables the `speechee` CLI command while you edit code.

```powershell
pip install -e .
```

### 4) Build whisper.cpp and download models

- Build engine: `engine/BUILD.md`
- Download models:

```powershell
python engine\model_manager.py recommended
```

### 5) Run the CLI

```powershell
speechee --help
```

### 6) Run the API server

```powershell
python api\server.py --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/ui`

## Running tests

This repo uses **script-style tests** (not a full pytest suite).

### Language tests

```powershell
python tests\test_language.py
```

### API tests

1) Start the API server:

```powershell
python api\server.py
```

2) Run:

```powershell
python tests\test_api.py
```

## Code style and conventions

### Python

- Keep changes small and focused.
- Prefer clear error messages and explicit validation.
- Keep imports at the top of files.

### CLI

- Keep CLI commands discoverable via `--help`.
- Prefer backwards-compatible CLI flags.

### API

- Endpoint behavior should be stable.
- Validate inputs and return clear error responses.

### Documentation

- Update relevant docs under `docs/` when behavior changes.
- If you add a new top-level module/folder, also add `docs/README.md` under that folder.

## Submitting changes

### 1) Create a branch

```text
feature/<short-name>
fix/<short-name>
docs/<short-name>
```

### 2) Verify before opening a PR

- Run the relevant test scripts under `tests/`
- Manually run:
  - `speechee info`
  - One local transcription flow (`speechee transcribe ...`)

### 3) Write a good PR description

Include:

- What changed and why
- How to test it
- Any breaking changes

## Reporting bugs / requesting features

Open an issue with:

- OS + Python version
- Exact command used
- Full error output
- Whether `engine/whisper.cpp/.../whisper-cli.exe` exists
- Which model(s) were installed under `engine/models/`
