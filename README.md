# Real-Time Local Voice Assistant (RTVA)

A fully local, low-latency, real-time conversational voice assistant running in Docker containers on Linux.

## Features

- 🎙️ **Speech-to-Text**: Faster-Whisper (GPU accelerated)
- 🧠 **LLM**: Mistral 7B via llama.cpp
- 🔊 **Text-to-Speech**: Coqui XTTS v2 with voice cloning
- ⚡ **Streaming Pipeline**: < 800ms perceived latency
- 🐳 **Docker**: Full containerization with NVIDIA runtime
- 🇫🇷 **French Support**: Default language with multilingual capabilities

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Audio Bridge│───▶│ STT Service │───▶│   LLM       │───▶│ TTS Service │
│   (C++)     │    │  (Whisper)  │    │  (llama.cpp)│    │   (XTTS)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                                      │                   │
       └──────────────────────────────────────┴───────────────────┘
                              │
                       ┌─────────────┐
                       │ Orchestrator│
                       └─────────────┘
```

## Quick Start

### Prerequisites

- Linux Mint (or Ubuntu 22.04)
- NVIDIA GPU (RTX 2080+)
- Docker with NVIDIA runtime
- CUDA 12.1

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/rtva.git
cd rtva

# Create models directory
mkdir -p models/whisper models/mistral models/xtts

# Download models (see below)

# Build and run
cd docker
docker compose up -d
```

### Download Models

```bash
# Whisper (small - ~140MB)
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cuda', compute_type='int8_float16')"

# Mistral 7B GGUF - Download from:
# https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
# Place as: models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# XTTS v2 - Auto-downloaded on first use
```

## Development

### Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Services Locally

```bash
# STT Service
cd src/stt_service
python -m service

# LLM Service
cd src/llm_service
./bin/server -m ../../models/mistral/mistral-7b.Q4_K_M.gguf --port 8002

# TTS Service
cd src/tts_service
python -m service

# Orchestrator
cd src/orchestrator
python -m pipeline
```

### Testing

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/
pytest tests/integration/
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_URL` | ws://localhost:8001/stt | STT service URL |
| `LLM_URL` | ws://localhost:8002/llm | LLM service URL |
| `TTS_URL` | ws://localhost:8003/tts | TTS service URL |
| `WHISPER_MODEL` | small | Whisper model size |
| `TTS_LANGUAGE` | fr | Default language |

## WebSocket API

### Orchestrator (Port 8000)

```javascript
// Start listening
{ "type": "listen_start" }

// Stop listening  
{ "type": "listen_stop" }

// Send transcription
{ "type": "transcription", "payload": { "text": "Hello", "is_final": true } }

// Receive audio
{ "type": "audio_output", "payload": { "data": "<base64>", "duration_ms": 2000 } }
```

## Performance Targets

| Stage | Target Latency |
|-------|---------------|
| STT processing | < 300ms |
| LLM first token | < 500ms |
| TTS first audio | < 300ms |
| **Total** | **< 800ms** |

## License

MIT
