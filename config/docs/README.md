# `config/` — Configuration Management

## Purpose

The `config/` package manages all Speechee configuration.

It provides:

- A defaults file (`defaults.json`) that defines baseline values
- A user override file (`config.json`) for local customization
- A `Settings` class that loads, merges, validates, and saves config

## Key files

- `defaults.json`
  - Baseline configuration shipped with the project
  - Intended to be treated as read-only
- `config.json`
  - User overrides
- `settings.py`
  - The `Settings` implementation (load/merge/get/set/save/validate)
- `__init__.py`
  - Exposes `Settings`, `get_settings`, and `get_config_value`

## Configuration layering

Speechee configuration is derived from:

1. `config/defaults.json`
2. `config/config.json`
3. Runtime updates via `Settings.set(...)`

## Access patterns

### Dot-path read

```python
from config import get_config_value

model = get_config_value("stt.model")
```

### Settings instance

```python
from config import get_settings

settings = get_settings()
threads = settings.get("stt.threads")
```

## Common keys

- `stt.*`: model, language, threads, translate
- `audio.*`: sample rate, channels, durations, device id
- `output.*`: formats and directories
- `models.*`: models directory and auto-download behavior
- `api.*`: host/port/CORS
- `performance.*`: thread and memory-related limits

## How this connects to other folders

- `cli/`: reads and updates settings via CLI commands
- `api/`: exposes config via `/config`
- `stt/` and `audio/`: read defaults/overrides to determine model/audio behaviors
- `engine/`: reads model directory paths

## Related documentation

- Installation: `docs/INSTALLATION.md`
- Usage: `docs/USAGE.md`
