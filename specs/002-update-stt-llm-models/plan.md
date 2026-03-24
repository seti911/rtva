# Implementation Plan: Update STT/LLM Models

**Branch**: `002-update-stt-llm-models` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)

## Summary

Replace STT (Whisper → Parakeet TDT 0.6B) and LLM (Mistral → CroissantLLMChat) models to fix hallucination issues and reduce memory footprint. TTS remains XTTS v2 for streaming support.

## Technical Context

**Language/Version**: Python 3.11+, C++  
**Primary Dependencies**: NeMo (Parakeet), llama.cpp (CroissantLLM), Coqui XTTS v2, WebSocket, Docker, CUDA 12.1  
**Storage**: N/A  
**Testing**: pytest, gtest  
**Target Platform**: Linux Mint with NVIDIA runtime (RTX 2080)  
**Project Type**: Multi-service Docker system  
**Performance Goals**: <800ms total perceived latency  
**Constraints**: Fully offline, GPU-accelerated, Docker containerized  
**Scale/Scope**: Single-user personal assistant

## Constitution Check

| Constitution Principle | Compliance | Notes |
|----------------------|------------|-------|
| I. Library-First | PASS | Each service self-contained |
| II. CLI Interface | PASS | Services expose CLI for testing |
| III. Test-First | PASS | TDD approach per spec |
| IV. Integration Testing | PASS | Pipeline tests required |
| V. Observability | PASS | Structured logging |
| VI. Versioning | PASS | Semantic versioning |
| VII. Simplicity | PASS | Smaller models = simpler |

## Project Structure

```text
src/
├── audio-bridge/        # C++ audio capture
├── stt-service/        # Python NeMo/Parakeet
├── llm-service/        # C++ llama.cpp
├── tts-service/        # Python XTTS
├── orchestrator/       # Python coordination
└── shared/            # Shared utilities

docker/
├── docker-compose.yml
└── [service].Dockerfile

models/
├── parakeet/          # TDT 0.6B
├── croissant/          # CroissantLLMChat GGUF
└── xtts/              # XTTS v2
```

## Implementation Tasks

### Phase 1: Model Updates

1. **STT Service Update**:
   - Replace faster-whisper with NVIDIA NeMo/Parakeet
   - Export to ONNX if needed
   - Update Docker to include NeMo dependencies

2. **LLM Service Update**:
   - Replace llama.cpp/Mistral with CroissantLLMChat GGUF
   - Update model loading to use GGUF
   - Reduce GPU memory usage

3. **TTS Service** (unchanged):
   - Keep XTTS v2 Docker setup

### Phase 2: Integration

4. **Update Docker Compose**:
   - New model paths
   - Memory/GPU allocation

5. **Test Pipeline**:
   - STT → LLM → TTS end-to-end
   - Latency measurement
   - Quality assessment

## Known Issues to Address

1. **Whisper Hallucination**: Fixed by using Parakeet TDT
2. **Mistral Size**: Fixed by using CroissantLLMChat (1.3B vs 7B)
3. **Audio Feedback Loop**: Use headphones during testing

## Next Steps

1. Download Parakeet TDT 0.6B model
2. Download CroissantLLMChat Q4_K_M GGUF
3. Update STT service to use NeMo
4. Update LLM service for GGUF loading
5. Build and test pipeline
