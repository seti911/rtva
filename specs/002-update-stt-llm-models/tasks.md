# Tasks: Update STT/LLM Models

**Feature**: 002-update-stt-llm-models  
**Generated**: 2026-03-24

## Dependency Graph

```
Phase 1 (Setup)
    │
    ├─► T001: Download Parakeet model
    ├─► T002: Download CroissantLLM GGUF
    │
Phase 2 (Foundational)
    │
    ├─► T003: Update STT Docker (NeMo)
    ├─► T004: Update LLM Docker (llama.cpp)
    │
Phase 3 (US1 - Voice Conversation)
    │
    ├─► T005: Replace STT service with Parakeet
    ├─► T006: Replace LLM service with CroissantLLM
    ├─► T007: Test pipeline end-to-end
    │
Phase 4 (Polish)
    │
    └─► T008: Verify latency meets <1s target
```

## Implementation Strategy

**MVP Scope**: Tasks T001-T007 (model updates + basic pipeline test)  
**Incremental Delivery**: Each model update (STT, LLM) tested independently before integration

---

## Phase 1: Setup

- [X] T001 Download Parakeet TDT 0.6B model to models/parakeet/
- [X] T002 Download CroissantLLMChat-v0.1-Q3_K_M GGUF to models/croissant/

---

## Phase 2: Foundational

- [X] T003 Update STT service Docker to include NeMo dependencies in src/stt_service/
- [X] T004 Update LLM service to load GGUF format in src/llm_service/

---

## Phase 3: User Story 1 - Voice Conversation

**Independent Test**: Speak into microphone, verify verbal response within 1 second

- [X] T005 [P] [US1] Replace faster-whisper with Parakeet TDT in src/stt_service/service.py
- [X] T006 [P] [US1] Replace Mistral with CroissantLLM in src/llm_service/
- [ ] T007 [US1] Test full pipeline: STT → LLM → TTS end-to-end

---

## Phase 4: Polish

**Independent Test**: System maintains <1s latency during 10+ minute conversation

- [ ] T008 Measure and verify end-to-end latency meets SC-001 (<1 second)

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 8 |
| Phase 1 (Setup) | 2 |
| Phase 2 (Foundational) | 2 |
| Phase 3 (US1) | 3 |
| Phase 4 (Polish) | 1 |
| Parallel Opportunities | 2 (T005, T006) |
