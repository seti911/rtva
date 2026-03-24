# Research: Update STT/LLM Models for Local Voice Assistant

## Technology Decisions

### 1. Speech-to-Text (STT): Parakeet TDT 0.6B v3

**Decision**: Use NVIDIA Parakeet TDT 0.6B v3 (nvidia/parakeet-tdt-0.6b-v3)

**Rationale**:
- 600M parameter FastConformer-TDT architecture
- Supports 25 EU languages with automatic detection
- Available in ONNX format for local inference
- Streaming support via NeMo chunked inference
- Average WER 6.34% on Open ASR Leaderboard (best for multilingual)
- No hallucination issues unlike Whisper

**Implementation**:
- Use NVIDIA NeMo for local inference
- Or use ONNX export via istupakov/parakeet-tdt-0.6b-v2-onnx
- Streaming mode with 2-second chunks

**Alternatives considered**:
- Whisper (rejected - hallucination issues)
- Canary-1B (larger, slower)

### 2. LLM: CroissantLLMChat-v0.1-GGUF

**Decision**: Use CroissantLLMChat-v0.1-GGUF (Q4_K_M quantization)

**Rationale**:
- 1.3B parameters (small, fits on consumer hardware)
- Truly bilingual French-English model
- GGUF format compatible with llama.cpp
- Q4_K_M quantization: ~812MB
- Chat model - ready for conversation
- Knowledge cutoff: November 2023
- Best for local deployment on RTX 2080

**Quantization Options**:
| Quantization | Size | Quality |
|--------------|------|---------|
| Q2_K | 576MB | Low |
| Q4_K_M | 872MB | Recommended |
| Q5_K_M | 932MB | High |

**Alternatives considered**:
- Mistral 7B (rejected - too large for RTX 2080 with other services)
- Qwen2.5-0.5B (not bilingual FR-EN)

### 3. Text-to-Speech (TTS): Coqui XTTS v2

**Decision**: Use Coqui XTTS v2 (unchanged from original spec)

**Rationale**:
- True streaming audio output
- Speaker cloning via reference WAV
- French language support
- 24kHz output quality

## Model Resource Requirements

| Model | Parameters | Memory (FP16) | Memory (Quantized) | GPU |
|-------|------------|---------------|-------------------|-----|
| Parakeet TDT 0.6B | 600M | ~1.2GB | ~1.2GB (ONNX) | RTX 2080 |
| CroissantLLMChat | 1.3B | ~2.6GB | ~0.9GB (Q4) | CPU or GPU |
| XTTS v2 | ~400M | ~800MB | ~800MB | RTX 2080 |
| **Total** | | **~4.6GB** | **~2.9GB** | |

**Note**: CroissantLLMChat can run on CPU since it's small enough, leaving GPU for STT+TTS.

## Streaming Pipeline Research

### Latency Budget

| Stage | Target Latency | Notes |
|-------|----------------|-------|
| Audio capture | <50ms | Buffer 500ms chunks |
| STT (Parakeet) | <300ms | GPU accelerated |
| LLM first token | <500ms | CPU acceptable |
| TTS (XTTS) | <300ms | GPU priority |
| Audio playback | <50ms | Non-blocking |

### Chunking Strategy

To simulate streaming TTS:
1. Buffer tokens until punctuation (.,!?)
2. Detect pauses in token stream (>200ms)
3. Max buffer: 20 tokens

## References

- [NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
- [Parakeet ONNX export](https://huggingface.co/istupakov/parakeet-tdt-0.6b-v2-onnx)
- [CroissantLLMChat GGUF](https://huggingface.co/croissantllm/CroissantLLMChat-v0.1-GGUF)
- [CroissantLLM Paper](https://arxiv.org/abs/2402.00786)
- [Coqui XTTS v2](https://github.com/coqui-ai/TTS)
