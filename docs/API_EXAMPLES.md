# API Usage Examples

These examples assume the API server is running at `http://127.0.0.1:8000`.

## Health check

```bash
curl http://127.0.0.1:8000/health
```

## Transcribe audio file (multipart)

```bash
curl -X POST http://127.0.0.1:8000/stt \
  -F "file=@tests/test_audio/jfk.wav" \
  -F "model=tiny.en" \
  -F "language=en" \
  -F "translate=false"
```

## Hindi transcription (keep Hindi text)

```bash
curl -X POST http://127.0.0.1:8000/stt \
  -F "file=@tests/test_audio/Hindi.wav" \
  -F "model=tiny" \
  -F "language=hi" \
  -F "translate=false"
```

## List models

```bash
curl http://127.0.0.1:8000/models
```

## List transcripts

```bash
curl "http://127.0.0.1:8000/transcripts?limit=10"
```

## Get a transcript content

```bash
curl http://127.0.0.1:8000/transcripts/transcript_20240101_120000.txt
```

## Delete a transcript

```bash
curl -X DELETE http://127.0.0.1:8000/transcripts/transcript_20240101_120000.txt
```
