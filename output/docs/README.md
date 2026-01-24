# `output/` — Runtime Artifacts

## Purpose

The `output/` folder stores runtime artifacts produced by Speechee:

- Temporary audio files (uploads and recordings)
- Saved transcript files

This folder is typically written to at runtime.

## Subfolders

- `output/temp/`
  - Temporary WAV files and uploaded audio files used during transcription
- `output/transcripts/`
  - Saved transcripts produced by the CLI/API

## How files are created

- `api/`:
  - `POST /stt` saves uploaded audio under `output/temp/` and deletes it after transcription
- `stt/`:
  - `OutputManager.save(...)` writes to `output/transcripts/`
- `cli/`:
  - `--save` options write transcripts via `OutputManager`

## Managing outputs

Use the CLI:

```powershell
speechee outputs list
speechee outputs stats
speechee outputs clear --confirm
```

## Related documentation

- Usage: `docs/USAGE.md`
- CLI: `docs/CLI.md`
