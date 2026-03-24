# Research: Real-Time Local Voice Assistant

## Technology Decisions

### 1. Speech-to-Text (STT): Parakeet TDT 06.B

**Decision**: Use ONNX or CPU-optimized version

**Rationale**:
- GPU-accelerated via CUDA
- Supports streaming transcription
- Smaller models (small: ~140MB, medium: ~1.5GB) fit on RTX 2080
- int8_float16 compute type balances speed and accuracy

**Alternatives evaluated**:
- Kyutai 

### 2. LLM: llama.cpp with Mistral 7B

**Decision**: Use Mistral 7B Instruct GGUF (Q4_K_M quantization)

**Rationale**:
- Excellent instruction-following for conversational AI
- Q4_K_M quantization reduces memory to ~4GB while maintaining quality
- llama.cpp provides excellent token streaming
- Can run on CPU to leave GPU for TTS

**Alternatives evaluated**:
- CroissantLLMChat-v0.1-GGUF

### 3. Text-to-Speech (TTS): Coqui XTTS v2

**Decision**: Use Coqui XTTS v2

**Rationale**:
- True streaming audio output
- Speaker cloning via reference WAV
- French language support
- 24kHz output quality

**Alternatives evaluated**:
- no alternative

### 4. Audio Bridge: C++ with miniaudio

**Decision**: Use C++ with miniaudio library

**Rationale**:
- Cross-platform (Linux, macOS, Windows)
- Low-latency audio capture/playback
- Simple API for PCM 16-bit mono
- Thread-safe, non-blocking options

### 5. Inter-Service Communication: WebSockets

**Decision**: Use WebSockets for all streaming communication

**Rationale**:
- Full-duplex communication for streaming
- Native browser/JSON compatibility
- Good library support (websockets Python, websockets-libcurl C++)

### 6. Containerization: Docker with NVIDIA runtime

**Decision**: Docker Compose with NVIDIA runtime

**Rationale**:
- GPU access via nvidia-docker
- Service isolation
- Reproducible deployment

## Streaming Pipeline Research

### Latency Budget Allocation

| Stage | Target Latency | Notes |
|-------|----------------|-------|
| Audio capture | <50ms | Buffer 500ms chunks |
| STT processing | <300ms | GPU accelerated |
| LLM first token | <500ms | CPU acceptable |
| TTS generation | <300ms | GPU priority |
| Audio playback | <50ms | Non-blocking |

### Phrase Chunking Strategy

To simulate streaming TTS:
1. Buffer tokens until punctuation (.,!?)
2. Detect pauses in token stream (>200ms)
3. Max buffer: 20 tokens

## GPU Scheduling

RTX 2080 constraints:
- Cannot run STT + TTS simultaneously at full load
- Priority: TTS > STT
- LLM runs on CPU by default

## References

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Coqui XTTS](https://github.com/coqui-ai/TTS)
- [miniaudio](https://github.com/dr-soft/miniaudio)
- [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
