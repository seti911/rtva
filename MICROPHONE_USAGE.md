# French Voice Assistant - Microphone Client

Speak to your AI and get a response in French! 🎤🇫🇷

## Quick Start

### 1. Ensure All Services Are Running

```bash
cd /home/stef/Development/localAI/rtva/docker
docker-compose up -d stt-service llm-service tts-service audio-bridge orchestrator
```

Check status:
```bash
docker-compose ps
```

### 2. Run the Voice Assistant

```bash
python3 /home/stef/Development/localAI/rtva/microphone_client.py
```

The assistant will:
1. Listen through your microphone for 5 seconds
2. Send audio to STT service
3. Process with LLM
4. Synthesize response with TTS
5. Play audio through speakers

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│        MICROPHONE VOICE ASSISTANT PIPELINE             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1️⃣  Speak into microphone (5 seconds)                  │
│      ↓                                                   │
│  2️⃣  Audio captured and sent to STT                     │
│      (Port 8001 - Speech-to-Text)                      │
│      ↓                                                   │
│  3️⃣  Transcribed text sent to LLM                       │
│      (Port 8002 - Language Model)                      │
│      ↓                                                   │
│  4️⃣  AI response generated and sent to TTS              │
│      (Port 8003 - Text-to-Speech)                      │
│      ↓                                                   │
│  5️⃣  Audio synthesized and played back                  │
│      through your speakers                             │
│      ↓                                                   │
│  ✅  Assistant responds! Listen and repeat...           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Example Conversation

```
======================================================================
FRENCH VOICE ASSISTANT - Microphone Client
======================================================================

──────────────────────────────────────────────────────────────────────
TURN 1
──────────────────────────────────────────────────────────────────────
🎤 Listening for 5.0 seconds...
  ✓ Recorded 219136 bytes

📝 Sending to STT service...
  ✓ You said: "Bonjour, comment allez-vous aujourd'hui?"

🧠 Thinking...
  ✓ AI said: "Bonjour! Ça va bien, merci de demander."

🔊 Synthesizing speech...
  ✓ Generated 87366 bytes of audio

🎵 Playing response...
  ✓ Done!
```

## Requirements

### System Audio Libraries

```bash
# On Ubuntu/Debian:
sudo apt-get install portaudio19-dev alsa-utils

# On macOS:
brew install portaudio

# On Windows:
# portaudio is included in Windows
```

### Python Libraries

```bash
# Install sounddevice for microphone input
pip install sounddevice

# Or alternatively, pyaudio:
pip install pyaudio
```

## Troubleshooting

### "No microphone detected"

```bash
# Check available audio devices
python3 << 'PYTHON'
import sounddevice as sd
print("Available audio devices:")
print(sd.query_devices())
PYTHON
```

### "sounddevice not available"

Install it:
```bash
pip install sounddevice
```

### Services not connecting

Check that all services are running:
```bash
cd /home/stef/Development/localAI/rtva/docker
docker-compose logs stt-service
docker-compose logs llm-service
docker-compose logs tts-service
```

### Audio playback not working

The client tries multiple methods:
1. `sounddevice` (recommended)
2. `aplay` (Linux fallback)

If neither works, audio is saved to `/tmp/response_audio.wav` and you can play it manually:
```bash
aplay /tmp/response_audio.wav
```

## Performance

Expected timings for each turn:

| Step | Time | Notes |
|------|------|-------|
| Microphone capture | 5.0s | User speaks |
| STT | 0.1-0.2s | Dummy STT (placeholder) |
| LLM inference | 1-2s | CroissantLLM generating response |
| TTS synthesis | 0.5-1.0s | Depends on response length |
| Audio playback | varies | Depends on synthesis length |
| **Total** | **6-8 seconds** | Per conversation turn |

With **real Parakeet-TDT 0.6B STT**, latency would be:
- STT: <50ms (streaming)
- Total: 2-4 seconds per turn

## Configuration

Edit `/home/stef/Development/localAI/rtva/microphone_client.py` to customize:

```python
assistant = MicrophoneVoiceAssistant(
    stt_url="ws://localhost:8001/stt",      # STT service
    llm_url="ws://localhost:8002/llm",      # LLM service
    tts_url="ws://localhost:8003/tts",      # TTS service
    sample_rate=16000,                       # Microphone sample rate
    chunk_size=4096,                         # Audio buffer size
)

# Run the voice assistant
await assistant.run(
    recording_duration=5.0,   # Record for 5 seconds per turn
    num_turns=-1              # Infinite turns (-1) or specific number
)
```

## Environment Variables

Optional environment variables:

```bash
# Customize service URLs
export STT_URL=ws://localhost:8001/stt
export LLM_URL=ws://localhost:8002/llm
export TTS_URL=ws://localhost:8003/tts

python3 microphone_client.py
```

## Tips for Best Results

1. **Speak clearly** - The STT service works best with clear speech
2. **Quiet environment** - Reduces background noise
3. **Standard microphone distance** - ~15-20cm from mic
4. **Use headphones** - Prevents audio feedback loops when listening to responses
5. **Check audio levels** - Test your microphone with: `python3 -c "import sounddevice as sd; print(sd.query_devices())"`

## Next Steps

1. **Deploy Real Parakeet-TDT 0.6B** - Replace dummy STT with actual speech recognition
2. **Add microphone input handler** - Integrate with orchest rator for automatic pipeline
3. **Implement wake word detection** - Start recording on trigger phrase
4. **Add persistence** - Save conversation history
5. **Language selection** - Support other languages besides French

## Useful Commands

Start all services:
```bash
cd /home/stef/Development/localAI/rtva/docker && docker-compose up -d
```

Stop all services:
```bash
cd /home/stef/Development/localAI/rtva/docker && docker-compose down
```

View service logs:
```bash
cd /home/stef/Development/localAI/rtva/docker && docker-compose logs -f [service-name]
```

Restart a specific service:
```bash
cd /home/stef/Development/localAI/rtva/docker && docker-compose restart stt-service
```

Run tests:
```bash
pytest tests/
```

---

**Enjoy your French voice assistant!** 🚀🎤
