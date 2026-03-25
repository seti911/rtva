#!/usr/bin/env python3
"""Live microphone input with push-to-talk (PTT) for French voice assistant."""

import asyncio
import websockets
import json
import base64
import numpy as np
import sounddevice as sd
import logging
from pynput import keyboard
import threading
from queue import Queue

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.05  # 50ms chunks for real-time response
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
TTS_SAMPLE_RATE = 24000

# PTT Settings
PTT_KEY = keyboard.Key.space

# Service URLs
STT_URL = "ws://localhost:8001"
LLM_URL = "ws://localhost:8002"
TTS_URL = "ws://localhost:8003"

# WebSocket settings - IMPORTANT: Increase max_size for large audio
WEBSOCKET_MAX_SIZE = 10 * 1024 * 1024  # 10MB max frame size

# Global state
ppt_event = threading.Event()
stop_recording_event = threading.Event()
audio_queue = Queue()
key_already_pressed = False  # Track if key was already pressed


def on_press(key):
    """Handle key press - only trigger once per press."""
    global key_already_pressed
    try:
        if key == PTT_KEY and not key_already_pressed:
            key_already_pressed = True
            ppt_event.set()
            stop_recording_event.clear()
    except AttributeError:
        pass


def on_release(key):
    """Handle key release."""
    global key_already_pressed
    try:
        if key == PTT_KEY:
            key_already_pressed = False
            stop_recording_event.set()
    except AttributeError:
        pass


def audio_callback(indata, frames, time_info, status):
    """Callback for sounddevice recording."""
    if status:
        logger.warning(f"Audio status: {status}")
    # Put a copy of the audio data into the queue
    audio_queue.put(indata.copy())


def get_audio_level(audio_chunk):
    """Get RMS level of audio chunk."""
    return np.sqrt(np.mean(audio_chunk**2))


async def record_with_ppt():
    """Record audio while PTT key is held down using non-blocking callback."""
    logger.info("🎤 Press and HOLD SPACE to record, release to stop\n")

    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    stream = None
    try:
        # Wait for key press
        logger.info("⏳ Waiting for key press...")
        ppt_event.clear()
        while not ppt_event.is_set():
            await asyncio.sleep(0.01)

        logger.info("🔴 RECORDING...\n")
        recorded_frames = []
        stop_recording_event.clear()

        # Start recording with callback (non-blocking)
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=CHUNK_SIZE,
            callback=audio_callback,
            dtype=np.float32,
        )
        stream.start()

        # Collect audio while recording
        while not stop_recording_event.is_set():
            try:
                # Get audio from queue (non-blocking with timeout)
                chunk = audio_queue.get(timeout=0.1)
                chunk = chunk.flatten()

                level = get_audio_level(chunk)
                recorded_frames.append(chunk)

                # Show level bar
                bar_length = int(level * 40)
                bar = "█" * bar_length + "░" * (40 - bar_length)
                logger.info(f"  {bar} {level:.4f}")
            except Exception:
                # Queue timeout, check if we should stop
                pass

            await asyncio.sleep(0.001)

        logger.info("\n⏹️  STOPPED\n")

        if recorded_frames:
            # Process the recorded audio
            audio_data = np.concatenate(recorded_frames)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            duration = len(audio_data) / SAMPLE_RATE
            logger.info(f"✓ Recorded {duration:.2f} seconds\n")

            return audio_int16.tobytes()

        return None

    finally:
        if stream:
            stream.stop()
            stream.close()
        listener.stop()


async def transcribe_audio(audio_bytes):
    """Send audio to STT service."""
    logger.info("📝 Transcribing (Parakeet-TDT)...")

    try:
        # Increase max_size for STT audio data
        async with websockets.connect(
            STT_URL, max_size=WEBSOCKET_MAX_SIZE
        ) as websocket:
            message = {
                "type": "audio",
                "payload": {
                    "pcm_data": base64.b64encode(audio_bytes).decode(),
                    "sample_rate": SAMPLE_RATE,
                },
            }

            await websocket.send(json.dumps(message))
            response_text = await asyncio.wait_for(websocket.recv(), timeout=10)
            response = json.loads(response_text)

            if response.get("type") == "transcription":
                text = response.get("payload", {}).get("text", "")
                if text:
                    logger.info(f'✓ You said: "{text}"\n')
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
        # Increase max_size for LLM responses
        async with websockets.connect(
            LLM_URL, ping_interval=None, max_size=WEBSOCKET_MAX_SIZE
        ) as websocket:
            message = {
                "type": "generate",
                "payload": {
                    "prompt": f"Vous êtes un assistant français utile et poli. Répondez brièvement en français (1-2 phrases). {user_text}",
                    "max_tokens": 150,
                    "temperature": 0.7,
                },
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
                        full_text = response.get("payload", {}).get(
                            "full_text", full_text
                        )
                        break

                except asyncio.TimeoutError:
                    break

            if full_text:
                logger.info(f'✓ AI said: "{full_text}"\n')
                return full_text

            logger.warning("❌ No LLM response received\n")
            return None

    except Exception as e:
        logger.error(f"❌ LLM error: {e}\n")
        return None


async def synthesize_and_play(text):
    """Synthesize speech and play audio."""
    logger.info("🔊 Synthesizing speech (XTTS v2)...")

    try:
        # CRITICAL: Increase max_size for TTS audio frames
        async with websockets.connect(
            TTS_URL, ping_interval=None, max_size=WEBSOCKET_MAX_SIZE
        ) as websocket:
            message = {
                "type": "synthesize",
                "payload": {"text": text, "language": "fr"},
            }

            await websocket.send(json.dumps(message))
            response_text = await asyncio.wait_for(websocket.recv(), timeout=30)
            response = json.loads(response_text)

            if response.get("type") == "audio":
                audio_b64 = response.get("payload", {}).get("audio_data", "")
                if audio_b64:
                    audio_data = base64.b64decode(audio_b64)
                    logger.info(f"✓ Generated audio")

                    # Convert to float32 - keep original 24kHz sample rate
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    logger.info(f"🎵 Playing at 24kHz...\n")
                    sd.play(audio_float32, TTS_SAMPLE_RATE)
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
    audio_bytes = await record_with_ppt()
    if not audio_bytes:
        logger.warning("⚠️  No audio recorded\n")
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
    logger.info("\nControls:")
    logger.info("  SPACE  = Press and hold to record")
    logger.info("  Ctrl+C = Quit\n")

    turn = 1

    try:
        while True:
            await conversation_turn(turn)
            turn += 1

    except KeyboardInterrupt:
        logger.info("\n\n👋 Goodbye!\n")


if __name__ == "__main__":
    asyncio.run(main())
