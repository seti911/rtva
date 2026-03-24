# STT Service Contract

## Service Information

- **Name**: stt-service
- **Port**: 8001
- **Protocol**: WebSocket
- **Base Image**: nvidia/cuda:12.1.1-runtime-ubuntu22.04

## WebSocket Endpoint

```
ws://localhost:8001/stt
```

## Messages: Client → STT Service

### Start Stream

```json
{
  "type": "start",
  "model": "small",
  "language": "fr",
  "compute_type": "int8_float16"
}
```

### Audio Chunk

```json
{
  "type": "audio",
  "data": "<base64 encoded PCM16 mono 16kHz>",
  "timestamp": 12345
}
```

### Stop Stream

```json
{
  "type": "stop"
}
```

## Messages: STT Service → Client

### Transcription Partial

```json
{
  "type": "transcription",
  "text": "partial text",
  "is_final": false,
  "confidence": 0.85,
  "timestamp_start": 0,
  "timestamp_end": 500
}
```

### Transcription Final

```json
{
  "type": "transcription", 
  "text": "complete sentence",
  "is_final": true,
  "confidence": 0.92,
  "timestamp_start": 0,
  "timestamp_end": 2000
}
```

### Error

```json
{
  "type": "error",
  "message": "Error description"
}
```

## Requirements

- Audio format: PCM 16-bit mono, 16kHz
- Chunk size: 500ms (8000 bytes)
- Latency target: <300ms processing time
- GPU: CUDA required
