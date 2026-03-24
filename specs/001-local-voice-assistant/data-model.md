# Data Model: Real-Time Voice Assistant

## Core Data Structures

### Audio Input Stream

```python
AudioInputChunk {
    timestamp: int          # milliseconds since start
    pcm_data: bytes         # 16-bit PCM mono 16kHz
    chunk_duration_ms: int  # typically 500ms
    sample_rate: int        # 16000
    channels: int           # 1 (mono)
    format: str             # "pcm16"
}
```

### Transcription

```python
TranscriptionPartial {
    text: str               # incremental text
    is_final: bool          # true when segment complete
    timestamp_start: int    # ms
    timestamp_end: int      # ms
    confidence: float       # 0.0-1.0
}
```

### LLM Request/Response

```python
LLMRequest {
    prompt: str             # full conversation context
    max_tokens: int         # typically 256
    temperature: float      # 0.7 default
    stream: bool            # must be true
}

LLMToken {
    token: str              # decoded token
    is_final: bool          # end of response marker
    timestamp: int          # when token generated
}
```

### TTS Input/Output

```python
TTSRequest {
    text: str               # text to synthesize
    language: str           # "fr" default
    reference_wav: bytes   # optional voice clone
    stream: bool           # true for streaming
}

TTSAudioChunk {
    audio_data: bytes       # 24kHz float32 or PCM16
    is_final: bool         # end of audio
    duration_ms: int       # chunk duration
}
```

## Service Interfaces

### Audio Bridge → STT Service

```python
# WebSocket message types
WS_AUDIO_CHUNK = "audio_chunk"
WS_TRANSCRIPTION = "transcription"
WS_CONTROL = "control"  # start, stop, pause

# Outbound (Audio Bridge → STT)
{
    "type": "audio_chunk",
    "payload": {
        "timestamp": 12345,
        "pcm_data": "<base64 encoded audio>",
        "chunk_duration_ms": 500
    }
}

# Inbound (STT → Audio Bridge)  
{
    "type": "transcription",
    "payload": {
        "text": "Hello",
        "is_final": False,
        "confidence": 0.95
    }
}
```

### Orchestrator → LLM Service

```python
# WebSocket message types
WS_LLM_REQUEST = "llm_request"
WS_LLM_TOKEN = "llm_token"
WS_LLM_CONTROL = "control"

# Outbound (Orchestrator → LLM)
{
    "type": "llm_request",
    "payload": {
        "prompt": "[INST] User said: hello\n Assistant:",
        "max_tokens": 256,
        "temperature": 0.7
    }
}

# Inbound (LLM → Orchestrator)
{
    "type": "llm_token", 
    "payload": {
        "token": "Hello",
        "is_final": False
    }
}
```

### Orchestrator → TTS Service

```python
# Outbound (Orchestrator → TTS)
{
    "type": "tts_request",
    "payload": {
        "text": "Hello, how can I help?",
        "language": "fr",
        "reference_wav": "<optional base64>"
    }
}

# Inbound (TTS → Orchestrator)
{
    "type": "tts_audio",
    "payload": {
        "audio_data": "<base64 audio>",
        "is_final": False,
        "duration_ms": 1500
    }
}
```

## State Machines

### Conversation State

```
IDLE → LISTENING → PROCESSING → SPEAKING → LISTENING
                    ↓
               INTERRUPTED
```

### Pipeline State

```
AUDIO_INPUT → STT_PROCESSING → LLM_PROCESSING → TTS_PROCESSING → AUDIO_OUTPUT
     ↓              ↓                ↓                ↓
  RUNNING        RUNNING          RUNNING          RUNNING
```

## Validation Rules

| Field | Rule |
|-------|------|
| Audio chunk size | Must be exactly (sample_rate × channels × bytes_per_sample × duration_ms / 1000) |
| Sample rate | Must be 16000 (input) or 24000 (output) |
| Text encoding | UTF-8 required |
| Token buffer | Max 20 tokens before forced TTS trigger |
| Latency threshold | Each stage must complete within 500ms |
