# Supported Commands

This document summarizes the commands you can run in this repository.

## Primary command: `speechee`

If installed (recommended):

```powershell
pip install -e .
speechee --help
```

If not installed:

```powershell
python cli\speechee.py --help
```

### Commands

- `speechee listen`
- `speechee transcribe <file>`
- `speechee record`
- `speechee models [list|download|verify|recommended|all]`
- `speechee devices`
- `speechee outputs [list|stats|clear]`
- `speechee config [show|get|set|reset|validate|path]`
- `speechee info`
- `speechee language [detect|list|model]`
- `speechee api`

## Engine (standalone)

- Build instructions: `engine/BUILD.md`
- Model manager:

```powershell
python engine\model_manager.py help
```

## Tools

- Resource monitor:

```powershell
python tools\monitor.py --help
```

- Benchmarks:

```powershell
python tools\benchmark.py --help
```

## Tests

- API test script:

```powershell
python tests\test_api.py
```

- Language tests:

```powershell
python tests\test_language.py
```
