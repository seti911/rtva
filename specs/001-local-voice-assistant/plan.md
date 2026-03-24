# Implementation Plan: Real-Time Local Voice Assistant

**Branch**: `001-local-voice-assistant` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-local-voice-assistant/`

## Summary

Build a fully local, low-latency (<800ms perceived), real-time conversational voice assistant running in Docker containers on Linux. The system uses a streaming pipeline: Audio Input → STT (faster-whisper) → LLM (llama.cpp/Mistral) → TTS (Coqui XTTS v2) → Audio Output. All stages must be fully streaming and parallel.

## Technical Context

**Language/Version**: Python 3.11+, C++  
**Primary Dependencies**: faster-whisper, llama.cpp, Coqui XTTS v2, WebSocket (websockets library), Docker, CUDA 12.1  
**Storage**: N/A (no persistent storage required for core functionality)  
**Testing**: pytest for Python services, gtest for C++ audio bridge  
**Target Platform**: Linux Mint with NVIDIA runtime (RTX 2080)  
**Project Type**: Multi-service system (microservices architecture in Docker)  
**Performance Goals**: <800ms total perceived latency, streaming at all pipeline stages  
**Constraints**: Fully offline, GPU-accelerated (RTX 2080), Docker containerized  
**Scale/Scope**: Single-user personal assistant, 5 core services

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance | Notes |
|----------------------|------------|-------|
| I. Library-First | PASS | Each service (STT, LLM, TTS, Orchestrator) is self-contained |
| II. CLI Interface | PASS | Each service exposes CLI for testing |
| III. Test-First | PASS | TDD approach: tests defined in spec before implementation |
| IV. Integration Testing | PASS | Pipeline integration tests required |
| V. Observability | PASS | Structured logging, latency metrics |
| VI. Versioning | PASS | Semantic versioning for releases |
| VII. Simplicity | PASS | Minimal dependencies, YAGNI |

## Project Structure

### Documentation (this feature)

```text
specs/001-local-voice-assistant/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── audio-bridge/        # C++ audio capture/playback
│   ├── include/
│   ├── src/
│   └── tests/
├── stt-service/         # Python faster-whisper service
│   ├── src/
│   └── tests/
├── llm-service/         # C++ llama.cpp service
│   ├── include/
│   ├── src/
│   └── tests/
├── tts-service/         # Python Coqui XTTS service
│   ├── src/
│   └── tests/
├── orchestrator/        # Python coordination service
│   ├── src/
│   └── tests/
└── shared/              # Shared utilities, protocols

docker/
├── docker-compose.yml
├── stt.Dockerfile
├── llm.Dockerfile
├── tts.Dockerfile
└── orchestrator.Dockerfile

models/                  # Downloaded models (gitignored)
├── whisper/
├── mistral/
└── xtts/
```

**Structure Decision**: Multi-service architecture with 5 isolated services + 1 shared utility module. Each service in its own directory with independent tests. Docker Compose for orchestration.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution principles are satisfied.

## Phase 0: Research (COMPLETED)

Key research areas completed:
1. faster-whisper streaming implementation patterns
2. llama.cpp WebSocket server integration
3. Coqui XTTS v2 streaming latency optimization
4. WebSocket audio streaming protocols
5. Non-blocking audio I/O in C++ (miniaudio/PortAudio)
6. Docker NVIDIA runtime best practices

## Phase 1: Design Artifacts (COMPLETED)

- `research.md`: Technology selection rationale ✓
- `data-model.md`: Pipeline data structures ✓
- `quickstart.md`: Development setup guide ✓
- `contracts/`: Service interface definitions ✓

## Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Setup | COMPLETE | Directory structure, Docker, Python venv |
| Phase 2: Foundational | COMPLETE | Shared protocols, Docker networking, models downloaded |
| Phase 3: US1 - Voice Conversation | COMPLETE | Core pipeline working |
| Phase 4: US2 - Continuous Listening | IN PROGRESS | VAD implementation |
| Phase 5: US3 - Natural Pacing | PENDING | Chunking, fillers |
| Phase 6: US4 - Multi-Language | PENDING | Language config, voice cloning |
| Phase 7: Polish | PENDING | Logging, metrics, optimization |

## Known Issues

1. **Whisper Hallucination**: faster-whisper-small/medium exhibits hallucination on silence ("Sous-titres réalisés par la communauté d'Amara.org"). Solutions: filter in code, use larger model, or better audio preprocessing.

2. **Audio Feedback**: Speaker output picked up by microphone causes loops. Requires headphones or acoustic isolation.

3. **Latency**: Current end-to-end ~2-3 seconds, target is <1 second. Needs optimization.

## Next Steps

1. Fix STT hallucination with post-processing filter
2. Implement continuous listening (US2)
3. Add proper audio device selection in audio-bridge
4. Optimize latency to meet <1s target
