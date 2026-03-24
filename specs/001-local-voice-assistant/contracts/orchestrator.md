# Orchestrator Service Contract

## Service Information

- **Name**: orchestrator
- **Port**: 8000
- **Protocol**: WebSocket
- **Purpose**: Coordinate all services, manage pipeline

## WebSocket Endpoint

```
ws://localhost:8000/ws
```

## Messages: Client → Orchestrator

### Start Listening

```json
{
  "type": "listen_start"
}
```

### Stop Listening

```json
{
  "type": "listen_stop"
}
```

### Interrupt (user starts speaking)

```json
{
  "type": "interrupt"
}
```

### Set Configuration

```json
{
  "type": "config",
  "payload": {
    "language": "fr",
    "voice_reference": "<optional base64>",
    "llm_temperature": 0.7,
    "stt_model": "small"
  }
}
```

## Messages: Orchestrator → Client

### Pipeline Status

```json
{
  "type": "status",
  "state": "idle|listening|processing|speaking|interrupted",
  "latency_ms": 450
}
```

### Transcription Received

```json
{
  "type": "transcription",
  "text": "Hello",
  "is_final": false
}
```

### Audio Output (final)

```json
{
  "type": "audio_output",
  "data": "<base64 encoded audio>",
  "duration_ms": 2000
}
```

### Error

```json
{
  "type": "error",
  "message": "Error description",
  "code": "STT_ERROR|LLM_ERROR|TTS_ERROR|AUDIO_ERROR"
}
```

## Internal Pipeline

The orchestrator manages these connections:
- STT Service: ws://stt-service:8001/stt
- LLM Service: ws://llm-service:8002/llm  
- TTS Service: ws://tts-service:8003/tts

## Requirements

- Latency tracking: Required
- Error handling: Graceful degradation
- State management: Thread-safe
- Buffering: Non-blocking queues between stages
