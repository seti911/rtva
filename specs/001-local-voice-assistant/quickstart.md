# Quickstart: Real-Time Voice Assistant

## Prerequisites

- Linux Mint (or Ubuntu 22.04)
- NVIDIA GPU (RTX 2080 or equivalent)
- Docker with NVIDIA runtime
- CUDA 12.1
- Python 3.11+
- C++ compiler (g++)

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-repo/rtva.git
cd rtva

# Create models directory
mkdir -p models/whisper models/mistral models/xtts
```

### 2. Download Models

```bash
# Download Whisper model (small)
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cuda', compute_type='int8_float16')"

# Download Mistral 7B GGUF
# From https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
# Place mistral-7b-instruct-v0.2.Q4_K_M.gguf in models/mistral/

# Download XTTS model
# From https://huggingface.co/coqui/XTTS-v2
# Place in models/xtts/
```

### 3. Build Docker Images

```bash
cd docker
docker compose build
```

### 4. Run Services

```bash
# Start all services
docker compose up -d

# Check logs
docker compose logs -f
```

### 5. Test Pipeline

```bash
# Connect to orchestrator WebSocket
ws://localhost:8000/ws

# Send test transcription
{"type": "transcription", "payload": {"text": "Hello", "is_final": true}}

# Listen for audio response on output stream
```

## Development Setup

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install faster-whisper websockets coqui-tts

# Install audio bridge dependencies
sudo apt-get install libasound2-dev

# Build audio bridge
cd src/audio-bridge
mkdir build && cd build
cmake .. && make
```

### Running Individual Services

```bash
# STT Service
cd src/stt-service
python -m stt_service

# LLM Service  
cd src/llm-service
./llm-service --model ../models/mistral/mistral-7b.Q4_K_M.gguf

# TTS Service
cd src/tts-service
python -m tts_service

# Orchestrator
cd src/orchestrator
python -m orchestrator
```

## Testing

```bash
# Run unit tests
pytest src/*/tests/

# Run integration tests
pytest tests/integration/

# Test audio pipeline
./scripts/test_pipeline.sh
```

## Configuration

Environment variables:
- `WHISPER_MODEL`: Model size (default: small)
- `LLM_MODEL_PATH`: Path to GGUF model
- `TTS_LANGUAGE`: Default language (default: fr)
- `WS_HOST`: WebSocket host (default: 0.0.0.0)
- `WS_PORT`: WebSocket port (default: 8000)

## Troubleshooting

### GPU Not Available
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-slm
```

### Audio Device Not Found
```bash
# List audio devices
arecord -l
aplay -l
```

### High Latency
- Reduce chunk size (500ms → 250ms)
- Use smaller Whisper model (medium → small)
- Run LLM on CPU
