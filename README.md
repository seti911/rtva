# Real-Time Local Voice Assistant (RTVA)

A fully local, low-latency, real-time conversational voice assistant with microphone input and audio playback. Runs in Docker containers on Linux with support for French language processing.

## Features

- 🎤 **Live Microphone Input**: Real-time audio capture with voice activity detection
- 🎙️ **Speech-to-Text**: STT service with Parakeet-TDT integration ready
- 🧠 **LLM**: CroissantLLM (3B parameters) for French language understanding
- 🔊 **Text-to-Speech**: Coqui XTTS v2 with natural voice synthesis
- ⚡ **Streaming Pipeline**: ~2-8s end-to-end latency
- 🐳 **Docker**: Full containerization with service orchestration
- 🇫🇷 **French Support**: Primary language with upgrade path for multilingual

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Audio Bridge│───▶│ STT Service │───▶│   LLM       │───▶│ TTS Service │
│   (C++)     │    │  (Parakeet) │    │  (llama.cpp)│    │   (XTTS)    │
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

- Linux (Ubuntu 20.04+, Linux Mint, etc.)
- Python 3.8+
- Audio hardware (microphone + speakers)
- Docker (optional, for containerized services)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/rtva.git
cd rtva

# Install dependencies
pip install -r requirements.txt

# Optional: Install audio support
pip install sounddevice
```

### Running the Assistant

#### Option 1: Docker (Recommended)
```bash
# Start all services
cd docker
docker-compose up -d

# Run microphone client
python3 microphone_client.py
```

#### Option 2: Local Python
```bash
# Start STT service
python3 src/stt_service/service.py &

# Start LLM service
python3 src/llm_service/service.py &

# Start TTS service
python3 src/tts_service/service.py &

# Run microphone client
python3 microphone_client.py
```

#### Option 3: Run Existing Tests
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## Project Structure

```
rtva/
├── microphone_client.py           # Main entry point - runs voice assistant
├── src/
│   ├── stt_service/              # Speech-to-Text service
│   ├── llm_service/              # Language Model service (CroissantLLM)
│   ├── tts_service/              # Text-to-Speech service (XTTS v2)
│   ├── orchestrator/             # Pipeline orchestration
│   └── shared/                   # Shared protocol definitions
├── docker/                        # Docker compose files & service configurations
├── models/                        # Model cache directory
│   ├── croissant/                # CroissantLLM model files
│   └── sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/  # Parakeet STT model
├── tests/                         # Test suite (unit & integration)
├── specs/                         # Project specifications
└── scripts/                       # Utility scripts
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# Run with coverage
pytest --cov=src
```

### Service Ports

- **8001**: STT Service (Speech-to-Text)
- **8002**: LLM Service (Language Model)
- **8003**: TTS Service (Text-to-Speech)

## Configuration

Environment variables for service URLs:

```bash
STT_SERVICE_URL=ws://localhost:8001  # Speech-to-Text
LLM_SERVICE_URL=ws://localhost:8002  # Language Model
TTS_SERVICE_URL=ws://localhost:8003  # Text-to-Speech
```

## Performance

### Current Latency (with CroissantLLM + XTTS v2)

| Component | Latency |
|-----------|---------|
| Microphone capture | 5.0s (user speaks) |
| STT processing | 0.1s (dummy placeholder) |
| LLM inference | 1-2s |
| TTS synthesis | 0.5-1.0s |
| **Total per turn** | **6-8s** |

### With Real Parakeet-TDT 0.6B (After Integration)

| Component | Latency |
|-----------|---------|
| Microphone capture | 5.0s |
| STT processing | <50ms (streaming) |
| LLM inference | 1-2s |
| TTS synthesis | 0.5-1.0s |
| **Total per turn** | **2-4s** |

## API Protocol

Services communicate via WebSocket with message format:

```json
{
  "type": "message_type",
  "payload": {
    "text": "content",
    "language": "fr"
  }
}
```

See `src/shared/protocol.py` for full protocol specification.

## License

MIT
