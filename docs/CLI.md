# CLI Reference

The Speechee CLI is the primary developer interface for local/offline usage.

Entry point:

- Python: `cli/speechee.py`
- Installed command: `speechee` (via `setup.py` console script)

## Basic usage

```text
speechee <command> [options]
```

## Commands

## `speechee listen`

Record from microphone and transcribe.

Inputs:

- Microphone audio (via `sounddevice` or `pyaudio`)

Options:

- `-d/--duration <seconds>`
- `-m/--model <name>`
- `-l/--language <code|auto>`
- `--save`
- `-f/--format <txt|json|srt|vtt>`
- `--keep-audio`
- `--verbose`

Outputs:

- Prints transcript to stdout
- Optionally saves transcript via `stt.OutputManager`

## `speechee transcribe FILE`

Transcribe an existing audio file.

Options:

- `-m/--model <name>`
- `-l/--language <code|auto>`
- `-o/--output <path>`: write plain transcript text to a file
- `--save`: save to `output/transcripts/`
- `-f/--format <txt|json|srt|vtt>`
- `--verbose`

## `speechee record`

Record audio and save it as a WAV file.

Options:

- `-d/--duration <seconds>`
- `-o/--output <filename>`

Output:

- WAV file under `output/temp/` unless a filename is specified

## `speechee models`

Manage model files in `engine/models/`.

Subcommands:

- `list` (default)
- `download <name>`
- `verify [name]`
- `recommended`
- `all`

Options:

- `--force`

## `speechee devices`

List audio input devices (useful for debugging microphone issues).

## `speechee outputs`

Manage saved transcripts under `output/transcripts/`.

Subcommands:

- `list` (default)
- `stats`
- `clear --confirm`

Options:

- `--limit <n>`
- `--confirm`

## `speechee config`

Configuration management wrapper around `config.Settings`.

Subcommands:

- `show [section]`
- `get <key>`
- `set <key> <value>`
- `reset [key]`
- `validate`
- `path`

Config files:

- Defaults: `config/defaults.json`
- User overrides: `config/config.json`

## `speechee info`

Print a consolidated status:

- Whether the whisper binary exists
- Which models are downloaded
- Audio device availability

## `speechee language`

Language tools:

- `detect <text...>`
- `list`
- `model <language_code> [--quality fast|balanced|accurate]`

## `speechee api`

Start the FastAPI server.

Options:

- `--host` (default `127.0.0.1`)
- `--port` (default `8000`)
- `--reload`

## Exit codes

- `0`: success
- `1`: failure

## Troubleshooting

See `docs/TROUBLESHOOTING.md`.
