# Platform / Device Requirements

Speechee is designed to work offline on low-end hardware.

## Supported platforms

- Windows 10/11 (primary target in this repository)

## Minimum recommended hardware

- CPU: Intel i3 (or equivalent)
- RAM: 4 GB
- Storage: 1–3 GB free (depending on model choices)

## Notes on model sizes

Model files are downloaded under `engine/models/`.

Typical sizes:

- `tiny.en` / `tiny`: ~75 MB
- `base`: ~142 MB
- `small`: ~466 MB

Larger models generally require more RAM and are slower.

## Audio requirements

Whisper works best with:

- 16 kHz
- mono

Speechee can convert/resample using `audio.AudioPreprocessor` if `soundfile` is installed.
