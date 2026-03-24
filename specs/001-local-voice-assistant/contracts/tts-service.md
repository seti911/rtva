# TTS Service Contract

## Service Information

- **Name**: tts-service
- **Port**: 8003
- **Protocol**: WebSocket
- **Base Image**: nvidia/cuda:12.1.1-runtime-ubuntu22.04

## WebSocket Endpoint

```
ws://localhost:8003/tts
```

## Messages: Client → TTS Service

### Synthesize Request

```json
{
  "type": "synthesize",
  "text": "Hello, how can I help you?",
  "language": "fr",
  "reference_wav": "<optional base64 encoded reference audio>",
  "stream": true
}
```

### Stop Synthesis

```json
{
  "type": "stop"
}
```

## Messages: TTS Service → Client

### Audio Chunk

```json
{
  "type": "audio",
  "data": "<base64 encoded audio>",
  "is_final": false,
  "duration_ms": 500
}
```

```json
{
  "type": "audio",
  "data": "<base64 encoded audio>",
  "is_final": true,
  "duration_ms": 1500
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

- Model: Coqui XTTS v2
- Audio output: 24kHz, float32 or PCM16
- Streaming: Required
- Latency target: <300ms first audio chunk
- Speaker cloning: Supported via reference WAV
- Language: French default, multilingual
- GPU: Required (priority over STT)
