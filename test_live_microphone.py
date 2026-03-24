#!/usr/bin/env python3
"""Live microphone input with TTS output for French voice assistant."""

import asyncio
import websockets
import json
import base64
import numpy as np
import sounddevice as sd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5  # seconds per chunk
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_THRESHOLD = 0.02  # amplitude threshold
MIN_SILENCE_DURATION = 1.0  # seconds of silence to end utterance

# Service URLs
STT_URL = "ws://localhost:8001"
LLM_URL = "ws://localhost:8002"
TTS_URL = "ws://localhost:8003"


def is_silent(audio_chunk, threshold=SILENCE_THRESHOLD):
    """Check if audio chunk is silent."""
    return np.max(np.abs(audio_chunk)) < threshold


async def record_utterance():
    """Record audio until silence is detected."""
    logger.info("🎤 Listening... (speak now, will stop after 1 second of silence)")
    
    recorded_frames = []
    silence_frames = 0
    max_silence_frames = int(MIN_SILENCE_DURATION / CHUNK_DURATION)
    speech_detected = False
    
    try:
        while True:
            # Record chunk
            chunk = sd.rec(CHUNK_SIZE, samplerate=SAMPLE_RATE, channels=1, dtype=np.float32)
            sd.wait()
            chunk = chunk.flatten()
            
            # Check for speech
            if is_silent(chunk):
                if speech_detected:
                    silence_frames += 1
                    logger.info(f"  Silence... ({silence_frames}/{max_silence_frames})")
                    if silence_frames >= max_silence_frames:
                        logger.info("✓ Recording complete\n")
                        break
            else:
                speech_detected = True
                silence_frames = 0
                recorded_frames.append(chunk)
                logger.info(f"  Recording... ({len(recorded_frames) * CHUNK_DURATION:.1f}s)")
        
        if not recorded_frames:
            logger.warning("No speech detected\n")
            return None
        
        # Combine frames
        audio_data = np.concatenate(recorded_frames)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        logger.info(f"✓ Recorded {len(audio_data) / SAMPLE_RATE:.1f} seconds\n")
        return audio_int16.tobytes()
        
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
            
            logger.warning("No transcription received\n")
            return None
            
    except Exception as e:
        logger.error(f"STT error: {e}\n")
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
            
            logger.warning("No LLM response received\n")
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
                    logger.info(f"✓ Generated audio, playing...\n")
                    
                    # Play audio
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
                    sd.play(audio_int16, SAMPLE_RATE)
                    sd.wait()
                    logger.info("✓ Done\n")
                    
                    return True
            
            logger.warning("No audio received from TTS\n")
            return False
            
    except Exception as e:
        logger.error(f"TTS error: {e}\n")
        return False


async def conversation_turn(turn_num):
    """Single conversation turn: record -> transcribe -> respond -> speak."""
    
    logger.info("─" * 75)
    logger.info(f"TURN {turn_num}")
    logger.info("─" * 75 + "\n")
    
    # Record speech
    audio_bytes = await record_utterance()
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
    logger.info("🎤 LIVE FRENCH VOICE ASSISTANT")
    logger.info("=" * 75)
    logger.info("\nPipeline: STT (Parakeet-TDT) → LLM (CroissantLLM) → TTS (XTTS)")
    logger.info("Press Ctrl+C to exit\n")
    
    turn = 1
    
    try:
        while True:
            success = await conversation_turn(turn)
            
            if not success:
                logger.warning("Turn failed, try again\n")
            
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
