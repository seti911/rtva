#!/usr/bin/env python3
"""End-to-end test with real TTS audio output."""

import asyncio
import websockets
import json
import base64
import os
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = 16000
STT_URL = "ws://localhost:8001"
LLM_URL = "ws://localhost:8002"
TTS_URL = "ws://localhost:8003"

# Test audio file
TEST_AUDIO_FILE = "/home/stef/Development/localAI/rtva/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/test_wavs/fr.wav"


async def transcribe_audio(audio_bytes):
    """Send audio to STT service."""
    logger.info("📝 Sending to STT service (Parakeet-TDT)...")
    
    try:
        async with websockets.connect(STT_URL) as websocket:
            message = {
                "type": "audio",
                "payload": {
                    "pcm_data": base64.b64encode(audio_bytes).decode(),
                    "sample_rate": SAMPLE_RATE
                }
            }
            
            await websocket.send(json.dumps(message))
            response_text = await asyncio.wait_for(websocket.recv(), timeout=10)
            response = json.loads(response_text)
            
            if response.get("type") == "transcription":
                text = response.get("payload", {}).get("text", "")
                if text:
                    logger.info(f"✓ Transcribed: \"{text}\"\n")
                    return text
            
            logger.warning("No transcription received")
            return None
            
    except Exception as e:
        logger.error(f"STT error: {e}\n")
        return None


async def get_llm_response(user_text):
    """Get response from LLM."""
    logger.info("🧠 Getting LLM response (CroissantLLM)...")
    
    try:
        async with websockets.connect(LLM_URL, ping_interval=None) as websocket:
            message = {
                "type": "generate",
                "payload": {
                    "prompt": f"Vous êtes un assistant français utile et poli. Répondez brièvement en français (1-2 phrases). {user_text}",
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            }
            
            await websocket.send(json.dumps(message))
            
            full_text = ""
            while True:
                try:
                    response_text = await asyncio.wait_for(websocket.recv(), timeout=30)
                    response = json.loads(response_text)
                    
                    if response.get("type") == "token":
                        token = response.get("payload", {}).get("token", "")
                        full_text += token
                    elif response.get("type") == "done":
                        full_text = response.get("payload", {}).get("full_text", full_text)
                        break
                    
                except asyncio.TimeoutError:
                    break
            
            if full_text:
                logger.info(f"✓ AI response: \"{full_text}\"\n")
                return full_text
            
            logger.warning("No LLM response received")
            return None
            
    except Exception as e:
        logger.error(f"LLM error: {e}\n")
        return None


async def synthesize_and_play(text):
    """Synthesize speech and play audio."""
    logger.info("🔊 Synthesizing speech (XTTS v2)...")
    
    try:
        async with websockets.connect(TTS_URL, ping_interval=None) as websocket:
            message = {
                "type": "synthesize",
                "payload": {
                    "text": text,
                    "language": "fr"
                }
            }
            
            await websocket.send(json.dumps(message))
            response_text = await asyncio.wait_for(websocket.recv(), timeout=30)
            response = json.loads(response_text)
            
            if response.get("type") == "audio":
                audio_b64 = response.get("payload", {}).get("audio_data", "")
                if audio_b64:
                    audio_data = base64.b64decode(audio_b64)
                    logger.info(f"✓ Generated {len(audio_data)} bytes of audio")
                    
                    # Play audio
                    logger.info("🎵 Playing response...\n")
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
                    sd.play(audio_int16, SAMPLE_RATE)
                    sd.wait()
                    logger.info("✓ Playback complete\n")
                    
                    return True
            
            logger.warning("No audio received from TTS")
            return False
            
    except Exception as e:
        logger.error(f"TTS error: {e}\n")
        return False


async def main():
    """Test end-to-end pipeline."""
    
    logger.info("=" * 75)
    logger.info("🎤 END-TO-END VOICE ASSISTANT TEST (REAL AUDIO)")
    logger.info("=" * 75)
    logger.info("\nPipeline: STT (Parakeet-TDT) → LLM (CroissantLLM) → TTS (XTTS)")
    logger.info(f"Using test audio: {os.path.basename(TEST_AUDIO_FILE)}\n")
    
    # Load test audio
    if not os.path.exists(TEST_AUDIO_FILE):
        logger.error(f"Test audio not found: {TEST_AUDIO_FILE}")
        return
    
    logger.info("─" * 75)
    logger.info("LOADING TEST AUDIO")
    logger.info("─" * 75 + "\n")
    
    try:
        sample_rate, audio_data = wavfile.read(TEST_AUDIO_FILE)
        
        # Convert to 16-bit if needed
        if audio_data.dtype != np.int16:
            max_val = np.abs(audio_data).max()
            audio_data = (audio_data / max_val * 32767).astype(np.int16)
        
        audio_bytes = audio_data.tobytes()
        duration = len(audio_data) / sample_rate
        logger.info(f"✓ Loaded {duration:.1f} seconds of audio ({len(audio_data)} samples)\n")
        
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        return
    
    # Run pipeline
    logger.info("─" * 75)
    logger.info("RUNNING PIPELINE")
    logger.info("─" * 75 + "\n")
    
    # Transcribe
    user_text = await transcribe_audio(audio_bytes)
    if not user_text:
        return
    
    # Get LLM response
    ai_text = await get_llm_response(user_text)
    if not ai_text:
        return
    
    # Synthesize and play
    await synthesize_and_play(ai_text)
    
    logger.info("=" * 75)
    logger.info("✅ END-TO-END TEST COMPLETE")
    logger.info("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
