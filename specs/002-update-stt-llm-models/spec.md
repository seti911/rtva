# Feature Specification: Update STT/LLM Models for Local Voice Assistant

**Feature Branch**: `002-update-stt-llm-models`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "whisper is not working as a STT because of hallucination, mistral is to big, so we need to read again new version of research.md and use Parakeet TDT 06B for STT and CroissantLLMChat-v0.1-GGUF for the LLM instead of Mistral. TTS has to be in streaming so xTTS is mandatory"

## User Scenarios & Testing

### User Story 1 - Voice Conversation Start (Priority: P1)

User speaks a question or command to the system, and the assistant responds verbally with minimal delay.

**Why this priority**: This is the core primary use case - the fundamental value proposition of the entire system.

**Independent Test**: Can be fully tested by speaking into the microphone and verifying verbal response is heard within 1 second.

**Acceptance Scenarios**:

1. **Given** the system is idle and listening, **When** the user speaks a complete sentence, **Then** the assistant begins verbal response within 1 second
2. **Given** the system is processing a response, **When** the user interrupts with new speech, **Then** the system stops current response and processes the new input

---

### User Story 2 - Continuous Listening (Priority: P1)

The system continuously monitors for voice input without requiring manual activation.

**Why this priority**: Natural conversation requires seamless back-and-forth without button presses or commands.

**Independent Test**: Can be tested by having multiple short exchanges without any manual intervention between them.

**Acceptance Scenarios**:

1. **Given** the system is running, **When** the user is silent, **Then** the system remains ready to receive input
2. **Given** the user finishes speaking, **When** a brief pause occurs, **Then** the system processes the input without additional user action

---

### User Story 3 - Natural Response Pacing (Priority: P2)

The assistant's speech sounds natural with appropriate pacing, fillers, and conversational rhythm.

**Why this priority**: Natural-sounding responses significantly improve user experience and perceived intelligence.

**Independent Test**: Can be evaluated by listening to responses and assessing whether they sound conversational rather than robotic.

**Acceptance Scenarios**:

1. **Given** the assistant generates a response, **When** the response includes conversational elements, **Then** speech output reflects natural pacing
2. **Given** multiple responses are generated, **When** the user evaluates them, **Then** responses feel fluid rather than stilted

---

### User Story 4 - Multi-Language Support (Priority: P3)

The assistant can understand and respond in multiple languages, with French as the default.

**Why this priority**: Users may need to communicate in their preferred language, particularly in multilingual regions.

**Independent Test**: Can be tested by speaking in different languages and verifying correct understanding and response.

**Acceptance Scenarios**:

1. **Given** the system is configured for French, **When** the user speaks in French, **Then** responses are in French
2. **Given** the user provides a reference voice sample, **When** the assistant speaks, **Then** output matches the reference voice characteristics

---

### Edge Cases

- What happens when no speech is detected for an extended period?
- How does the system handle background noise or poor audio quality?
- What occurs when the LLM generates an unexpectedly long response?
- How does the system behave when GPU resources are limited or unavailable?
- What happens if the audio input device is disconnected during use?

## Requirements

### Functional Requirements

- **FR-001**: System MUST capture microphone audio input in real-time
- **FR-002**: System MUST convert spoken language to text with less than 300ms latency
- **FR-003**: System MUST generate intelligent text responses using local AI models
- **FR-004**: System MUST convert text responses to speech with less than 300ms latency
- **FR-005**: System MUST play audio responses through speakers with minimal delay
- **FR-006**: The complete pipeline MUST respond to user speech within 1 second
- **FR-007**: System MUST stream audio continuously without waiting for complete sentences
- **FR-008**: System MUST operate entirely offline without internet connectivity
- **FR-009**: System MUST run within Docker containers on Linux
- **FR-010**: System MUST support speaker voice cloning via reference audio samples
- **FR-011**: System MUST use WebSocket protocol for all inter-service communication
- **FR-012**: System MUST handle multiple concurrent users without performance degradation

### Technology Updates (from original spec)

- **STT Model**: MUST use Parakeet TDT 06B instead of Whisper (to avoid hallucination)
- **LLM Model**: MUST use CroissantLLMChat-v0.1-GGUF instead of Mistral (smaller footprint)
- **TTS Model**: MUST use Coqui XTTS v2 for streaming audio output

### Key Entities

- **Audio Input Stream**: Continuous microphone data in PCM format
- **Transcription**: Converted text from speech, including partial results
- **Response Text**: Generated text from the AI model, streamed token-by-token
- **Audio Output Stream**: Synthesized speech audio data
- **Service Orchestrator**: Component coordinating all pipeline stages
- **Reference Voice Profile**: Audio sample used for voice cloning

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users experience less than 1 second delay between finishing speech and hearing assistant response begin
- **SC-002**: System processes continuous audio without dropping frames or losing input
- **SC-003**: Audio playback streams seamlessly without audible gaps or buffering
- **SC-004**: System maintains stable performance during extended conversations (10+ minutes)
- **SC-005**: Voice cloning produces recognizable similar voice to reference sample
- **SC-006**: System successfully handles at least 90% of common conversational queries
- **SC-007**: All processing occurs locally with zero external API calls during operation
- **SC-008**: Docker containers deploy and run successfully on Linux Mint with NVIDIA runtime

### Qualitative Outcomes

- **SC-009**: Conversation flow feels natural and responsive to users
- **SC-010**: System reliability meets expectations for daily personal assistant use

## Assumptions

- Parakeet TDT 06B is available in ONNX format for GPU acceleration
- CroissantLLMChat-v0.1-GGUF quantization fits in available RAM with other services
- XTTS v2 Docker image can be built with NVIDIA runtime support
- All models can run simultaneously on RTX 2080 with acceptable latency

## Dependencies

- NVIDIA CUDA 12.1+ runtime
- Docker with NVIDIA Docker support
- Linux host with audio input device
