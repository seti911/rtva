# LLM Service Contract

## Service Information

- **Name**: llm-service
- **Port**: 8002
- **Protocol**: WebSocket
- **Base Image**: nvidia/cuda:12.1.1-runtime-ubuntu22.04

## WebSocket Endpoint

```
ws://localhost:8002/llm
```

## Messages: Client → LLM Service

### Generate Request

```json
{
  "type": "generate",
  "prompt": "[INST] User said: hello\n Assistant:",
  "max_tokens": 256,
  "temperature": 0.7,
  "stream": true
}
```

### Stop Generation

```json
{
  "type": "stop"
}
```

## Messages: LLM Service → Client

### Token Stream

```json
{
  "type": "token",
  "token": "Hello",
  "is_final": false
}
```

```json
{
  "type": "token",
  "token": " there",
  "is_final": false
}
```

### Generation Complete

```json
{
  "type": "done",
  "full_text": "Hello there, how can I help you?",
  "tokens_generated": 42
}
```

### Error

```json
{
  "type": "error",
  "message": "Error description"
}
```

## Requirements

- Model: Mistral 7B Instruct GGUF (Q4_K_M)
- Quantization: Q4_K_M
- Streaming: Required (token-by-token)
- Latency target: <500ms first token
- GPU: Optional (can run on CPU)
