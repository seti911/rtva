#!/usr/bin/env python3
"""Test TTS and save audio to WAV file."""

import asyncio
import json
import base64
import websockets
import wave

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


def save_audio_wav(audio_bytes: bytes, filename: str = "tts_output.wav"):
    """Save raw PCM audio to WAV file."""
    try:
        with wave.open(filename, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(24000)  # 24kHz
            wav_file.writeframes(audio_bytes)
        print(f"✓ Audio saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving audio: {e}")
        return False


async def test_tts(question: str):
    print(f"Connecting to {ORCHESTRATOR_URL}...")
    try:
        async with websockets.connect(ORCHESTRATOR_URL) as ws:
            print("✓ Connected")

            await ws.send(json.dumps({"type": "listen_start"}))
            msg = await ws.recv()
            print(f"✓ Listen started")

            print(f'\nSending question: "{question}"')
            await ws.send(
                json.dumps(
                    {
                        "type": "transcription",
                        "payload": {"text": question, "is_final": True},
                    }
                )
            )

            print("\nLLM Response:")
            audio_received = False
            async for msg in ws:
                resp = json.loads(msg)
                t = resp.get("type")

                if t == "llm_token":
                    token = resp.get("payload", {}).get("token", "")
                    print(token, end="", flush=True)
                elif t == "audio_output":
                    audio_b64 = resp.get("payload", {}).get("data", "")
                    audio_bytes = base64.b64decode(audio_b64)
                    print(f"\n\n✓ Audio received ({len(audio_bytes)} bytes)")
                    save_audio_wav(audio_bytes)
                    audio_received = True
                    break

            if not audio_received:
                print("\n✗ No audio received")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys

    question = "Bonjour, comment allez-vous?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    asyncio.run(test_tts(question))
