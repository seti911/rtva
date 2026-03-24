#!/usr/bin/env python3
"""Live microphone input with push-to-talk (PTT) for French voice assistant."""

import asyncio
import websockets
import json
import base64
import numpy as np
import sounddevice as sd
from scipy import signal
import logging
import keyboard

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.05  # 50ms chunks for real-time response
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
TTS_SAMPLE_RATE = 24000

# PTT Settings
PTT_KEY = "space"  # Press SPACE to record

# Service URLs
STT_URL = "ws://localhost:8001"
LLM_URL = "ws://localhost:8002"
TTS_URL = "ws://localhost:8003"


def get_audio_level(audio_chunk):
    """Get RMS level of audio chunk."""
    return np.sqrt(np.mean(audio_chunk ** 2))


async def record_with_ptt():
    """Record audio while PTT key is held down."""
    logger.info(f"🎤 Press and HOLD '{PTT_KEY}' to record, release to stop\n")
    
    recorded_frames = []
    is_recording = False
    
    try:
        while True:
            # Check if PTT key is pressed
            if keyboard.is_pressed(PTT_KEY):
                if not is_recording:
                    is_recording = True
                    recorded_frames = []
                    logger.info("🔴 RECORDING...")
                
                # Record chunk while key is held
                chunk = sd.rec(CHUNK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype=np.float32)
                sd.wait()
                chunk = chunk.flatten()
                
                level = get_audio_level(chunk)
                recorded_frames.append(chunk)
                
                # Show level bar
                bar_length = int(level * 50)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                logger.info(f"  {bar} {level:.3f}")
            
            else:
                # Key released
                if is_recording:
                    is_recording = False
                    logger.info("⏹️  STOPPED\n")
                    
                    if recorded_frames:
                        # Process the recorded audio
                        audio_data = np.concatenate(recorded_frames)
                        audio_int16 = (audio_data * 32767).astype(np.int16)
                        
                        duration = len(audio_data) / SAMPLE_RATE
                        logger.info(f"✓ Recorded {duration:.1f} seconds\n")
                        
                        return audio_int16.tobytes()
                
                # Allow checking for menu commands
                if keyboard.is_pressed("q"):
                    logger.info("\nExiting...")
                    return None
                
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spam
        
    except KeyboardInterrupt:
        logger.info("Recording cancelled\n")
        return None


async def transcribe_audio(audio_bytes):
    """Send audio to STT service."""
    logger.info("📝 Transcribing (Parakeet-TDT)...")
    
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
                    logger.info(f"✓ You said: \"{text}\"\n")
                    return text
            
            logger.warning("❌ No transcription received\n")
            return None
            
    except Exception as e:
        logger.error(f"❌ STT error: {e}\n")
        return None


async def get_llm_response(user_text):
    """Get response from LLM."""
    logger.info("🧠 Thinking (CroissantLLM)...")
    
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
                logger.info(f"✓ AI said: \"{full_text}\"\n")
                return full_text
            
            logger.warning("❌ No LLM response received\n")
            return None
            
    except Exception as e:
        logger.error(f"❌ LLM error: {e}\n")
        return None


def resample_audio(audio_data, orig_sr, target_sr):
    """Resample audio."""
    if orig_sr == target_sr:
        return audio_data
    
    num_samples = int(len(audio_data) * target_sr / orig_sr)
    return signal.resample(audio_data, num_samples)


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
                    logger.info(f"✓ Generated audio")
                    
                    # Convert and resample
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0
                    audio_resampled = resample_audio(audio_float32, TTS_SAMPLE_RATE, SAMPLE_RATE)
                    
                    logger.info(f"🎵 Playing...\n")
                    sd.play(audio_resampled, SAMPLE_RATE)
                    sd.wait()
                    logger.info("✓ Done\n")
                    
                    return True
            
            logger.warning("❌ No audio received from TTS\n")
            return False
            
    except Exception as e:
        logger.error(f"❌ TTS error: {e}\n")
        return False


async def conversation_turn(turn_num):
    """Single conversation turn."""
    
    logger.info("─" * 75)
    logger.info(f"TURN {turn_num}")
    logger.info("─" * 75 + "\n")
    
    # Record speech (PTT)
    audio_bytes = await record_with_ptt()
    if not audio_bytes:
        return False
    
    # Transcribe
    user_text = await transcribe_audio(audio_bytes)
    if not user_text:
        return False
    
    # Get LLM response
    ai_text = await get_llm_response(user_text)
    if not ai_text:
        return False
    
    # Synthesize and play
    await synthesize_and_play(ai_text)
    
    return True


async def main():
    """Main conversation loop."""
    logger.info("=" * 75)
    logger.info("🎤 LIVE FRENCH VOICE ASSISTANT (PUSH-TO-TALK)")
    logger.info("=" * 75)
    logger.info("\nPipeline: STT (Parakeet-TDT) → LLM (CroissantLLM) → TTS (XTTS)")
    logger.info(f"Controls:")
    logger.info(f"  SPACE  = Press and hold to record")
    logger.info(f"  Q      = Quit\n")
    
    turn = 1
    
    try:
        while True:
            await conversation_turn(turn)
            turn += 1
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 75)
        logger.info("Conversation ended")
        logger.info("=" * 75)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
