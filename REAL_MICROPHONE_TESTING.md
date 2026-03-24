# 🎤 Real-Time Microphone Testing Guide

## Quick Start

To test the voice assistant with your microphone in real-time:

```bash
cd /home/stef/Development/localAI/rtva
source venv/bin/activate
python3 test_live_microphone.py
```

## How It Works

1. **Listens** for your voice (starts recording when sound detected)
2. **Stops recording** after 1 second of silence
3. **Transcribes** your speech using Parakeet-TDT (real speech-to-text)
4. **Processes** your request with CroissantLLM (AI response in French)
5. **Synthesizes** response using XTTS v2
6. **Plays** the audio response through your speakers

## Requirements

- ✅ Microphone connected and working
- ✅ Speakers/headphones connected  
- ✅ All Docker services running
- ✅ Python dependencies installed

### Check Docker Services

```bash
docker-compose -f docker/docker-compose.yml ps
```

All 5 services should show `Up`:
- `docker-stt-service-1` (Parakeet-TDT speech recognition)
- `docker-llm-service-1` (CroissantLLM AI responses)
- `docker-tts-service-1` (XTTS v2 speech synthesis)
- `docker-orchestrator-1`
- `docker-audio-bridge-1`

### Check Python Dependencies

```bash
source venv/bin/activate
python3 -c "import sounddevice, scipy, websockets; print('✓ Ready')"
```

## Test Scripts Available

### 1. **Live Microphone Test** (Recommended)
```bash
python3 test_live_microphone.py
```
Real-time conversation with voice input and audio output.

### 2. **End-to-End Test with Pre-recorded Audio**
```bash
python3 test_e2e_with_audio.py
```
Uses test French audio file instead of microphone (useful for debugging).

### 3. **Original Simulation Test**
```bash
python3 test_microphone_simulation.py
```
Tests pipeline with pre-recorded audio without audio playback.

## Troubleshooting

### No audio input detected
- Check microphone: `python3 -c "import sounddevice; print(sounddevice.query_devices())"`
- Try adjusting `SILENCE_THRESHOLD` in `test_live_microphone.py` (higher = less sensitive)

### No audio output
- Check speakers/headphones are connected
- Check volume levels
- Try: `python3 test_e2e_with_audio.py` to test TTS independently

### Services not responding
- Restart services: `docker-compose -f docker/docker-compose.yml restart`
- Check logs: `docker-compose -f docker/docker-compose.yml logs <service-name>`

### High latency
- STT: ~370ms per audio chunk (CPU processing)
- LLM: 2-10 seconds depending on response length
- TTS: 3-5 seconds for synthesis
- **Total**: ~5-20 seconds per turn (normal for CPU)

## Performance Notes

**Hardware**: CPU only (no GPU)

**Latency Breakdown**:
- Microphone recording: Until 1s of silence (~2-5 seconds typically)
- STT transcription: ~370ms (Parakeet-TDT is very fast!)
- LLM response: 2-10 seconds
- TTS synthesis: 3-5 seconds
- Audio playback: Duration of response

**Model Details**:
- **STT**: Parakeet-TDT 0.6B v3 (25 European languages)
- **LLM**: CroissantLLM (3B French language model)
- **TTS**: XTTS v2 (multilingual speech synthesis)

## Tips for Best Results

1. **Speak clearly** - The model is robust but clear speech helps
2. **Pause after speaking** - Wait for 1 second of silence to trigger processing
3. **Use French** - Trained primarily for French language
4. **Keep sentences short** - LLM responds faster to shorter prompts
5. **Check device volume** - May need to adjust input/output levels

## Example Conversation

```
User: "Bonjour, comment ca va?"
STT: "Bonjour, comment ça va?"
LLM: "Bonjour! Je vais bien, merci de demander. Comment puis-je vous aider?"
TTS: [Audio plays response in French]
```

## File Locations

- **Test scripts**: `/home/stef/Development/localAI/rtva/test_*.py`
- **STT service**: `/home/stef/Development/localAI/rtva/src/stt_service/service.py`
- **LLM service**: `/home/stef/Development/localAI/rtva/src/llm_service/service.py`
- **TTS service**: `/home/stef/Development/localAI/rtva/src/tts_service/service.py`
- **Models**: `/home/stef/Development/localAI/rtva/models/`

## Advanced Configuration

Edit the constants at the top of `test_live_microphone.py`:

```python
SAMPLE_RATE = 16000              # Audio sample rate
CHUNK_DURATION = 0.5              # Recording chunk size
SILENCE_THRESHOLD = 0.02           # Silence detection sensitivity (0-1)
MIN_SILENCE_DURATION = 1.0        # Silence duration to end recording (seconds)
```

---

**Enjoy your French voice assistant! 🎉**
