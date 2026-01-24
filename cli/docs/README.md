# `cli/` — Command Line Interface

## Purpose

The `cli/` package provides the user-facing command line interface for Speechee.

It is the easiest way to:

- Transcribe files
- Record and transcribe microphone audio
- Manage Whisper models
- Inspect devices and configuration
- Run the API server

## Key modules

- `speechee.py`
  - Main CLI entry point
  - Parses arguments and dispatches into `stt/`, `audio/`, `engine/`, and `config/`

## Public interface

If the package is installed (editable recommended), a `speechee` console script is available.

Otherwise, you can invoke the CLI directly:

```powershell
python cli\speechee.py --help
```

## Commands

See root docs:

- `docs/CLI.md`

## Configuration

The CLI reads configuration via `config.Settings` and supports commands to view/change settings.

Config files:

- `config/defaults.json`
- `config/config.json`

## How this connects to other folders

- `stt/`: transcription and output formatting
- `audio/`: recording and device enumeration
- `engine/`: model download/verify/list
- `config/`: settings retrieval and persistence
- `api/`: API server is started through CLI commands

## Related documentation

- CLI reference: `docs/CLI.md`
- Usage: `docs/USAGE.md`
