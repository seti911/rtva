# Tasks: Real-Time Local Voice Assistant

**Input**: Design documents from `/specs/001-local-voice-assistant/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per implementation plan in src/
- [X] T002 Create docker/ directory with docker-compose.yml and Dockerfiles
- [X] T003 Create models/ directory structure for whisper, mistral, xtts
- [X] T004 [P] Setup Python virtual environment with dependencies (faster-whisper, websockets, coqui-tts)
- [X] T005 [P] Configure pytest and testing infrastructure in tests/
- [ ] T006 Configure CMake for C++ audio bridge in src/audio-bridge/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create shared WebSocket protocol definitions in src/shared/protocol.py
- [X] T008 Implement audio data structures in src/shared/audio.py
- [X] T009 [P] Create base service class in src/shared/base_service.py
- [X] T010 [P] Setup Docker Compose networking between services
- [X] T011 Configure NVIDIA runtime for all Docker services
- [X] T012 Download and verify Whisper model in models/whisper/
- [ ] T013 Download and verify Mistral 7B GGUF model in models/mistral/
- [ ] T014 Download and verify XTTS v2 model in models/xtts/

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Voice Conversation Start (Priority: P1) 🎯 MVP

**Goal**: User speaks and receives verbal response within 1 second

**Independent Test**: Speak into microphone, verify verbal response starts within 1 second

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement C++ audio bridge capture in src/audio-bridge/src/capture.cpp
- [X] T016 [P] [US1] Implement C++ audio bridge playback in src/audio-bridge/src/playback.cpp
- [X] T017 [P] [US1] Create STT WebSocket client in src/stt_service/client.py
- [X] T018 [P] [US1] Create LLM WebSocket client in src/llm_service/client.py
- [X] T019 [P] [US1] Create TTS WebSocket client in src/tts_service/client.py
- [X] T020 [US1] Implement STT service in src/stt_service/service.py (depends on T015, T017)
- [X] T021 [US1] Implement LLM service in src/llm_service/service.py (depends on T018)
- [X] T022 [US1] Implement TTS service in src/tts_service/service.py (depends on T019)
- [X] T023 [US1] Implement orchestrator pipeline in src/orchestrator/pipeline.py
- [ ] T024 [US1] Connect audio bridge to STT service via WebSocket
- [X] T025 [US1] Connect orchestrator to LLM and TTS services
- [ ] T026 [US1] Verify end-to-end latency < 1 second

**Checkpoint**: At this point, User Story 1 should be fully functional and testable

---

## Phase 4: User Story 2 - Continuous Listening (Priority: P1)

**Goal**: System continuously monitors for voice input without manual activation

**Independent Test**: Multiple exchanges without any manual intervention

### Implementation for User Story 2

- [X] T027 [P] [US2] Implement voice activity detection (VAD) in src/stt_service/vad.py
- [ ] T028 [P] [US2] Add silence detection in audio bridge
- [ ] T029 [US2] Implement automatic listen state management in orchestrator
- [ ] T030 [US2] Handle transition from speaking to listening states
- [ ] T031 [US2] Test continuous conversation flow

**Checkpoint**: User Stories 1 AND 2 should work together seamlessly

---

## Phase 5: User Story 3 - Natural Response Pacing (Priority: P2)

**Goal**: Assistant speech sounds natural with appropriate pacing and fillers

**Independent Test**: Listen to responses and evaluate naturalness

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement phrase chunking logic in src/orchestrator/chunker.py
- [X] T033 [P] [US3] Add punctuation detection for TTS triggers
- [ ] T034 [US3] Modify LLM prompt to include conversational fillers
- [ ] T035 [US3] Implement token buffering for streaming TTS
- [ ] T036 [US3] Tune TTS trigger thresholds (punctuation, pause, max tokens)

**Checkpoint**: User Story 3 adds natural pacing to responses

---

## Phase 6: User Story 4 - Multi-Language Support (Priority: P3)

**Goal**: System understands and responds in French (default) with voice cloning

**Independent Test**: Speak in French, verify French response; provide reference WAV, verify voice match

### Implementation for User Story 4

- [ ] T037 [P] [US4] Add language configuration to orchestrator config
- [ ] T038 [P] [US4] Implement reference WAV handling in TTS service
- [ ] T039 [US4] Setup voice cloning with XTTS reference audio
- [ ] T040 [US4] Test French language responses
- [ ] T041 [US4] Test voice cloning functionality

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Add structured logging to all services
- [ ] T043 Implement latency metrics and monitoring
- [ ] T044 Add interrupt handling (user speaks over assistant)
- [ ] T045 [P] Update README.md with usage instructions
- [ ] T046 Update quickstart.md with final setup steps
- [ ] T047 Run integration tests for full pipeline
- [ ] T048 Performance optimization for latency targets

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational
  - User stories can proceed in parallel or sequentially by priority
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational - Core voice pipeline
- **US2 (P1)**: Starts after Foundational - Builds on US1 audio handling
- **US3 (P2)**: Starts after Foundational - Enhances US1 responses
- **US4 (P3)**: Starts after Foundational - Language/voice features

### Within Each User Story

- Audio bridge before service integration
- WebSocket clients before services
- Services before orchestrator pipeline
- Pipeline complete before testing

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- STT, LLM, TTS clients can be developed in parallel
- Language config and voice cloning can be parallelized in US4

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Voice Conversation)
4. **STOP and VALIDATE**: Test US1 independently - this is the MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test → Deploy/Demo (MVP!)
3. Add US2 → Test → Deploy/Demo
4. Add US3 → Test → Deploy/Demo
5. Add US4 → Test → Deploy/Demo

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
