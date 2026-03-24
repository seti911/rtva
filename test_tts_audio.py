#!/usr/bin/env python3
"""Test TTS by playing audio output."""

import asyncio
import json
import base64
import websockets
import numpy as np
import pyaudio

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


def play_audio(audio_bytes: bytes):
    """Play raw PCM audio at 24kHz."""
    try:
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
        stream.write(audio.tobytes())
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("✓ Audio played successfully")
    except Exception as e:
        print(f"Error playing audio: {e}")


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

                if t == "status":
                    state = resp.get("payload", {}).get("state")
                    if state != "listening":
                        print(f"[{state}]", end=" ", flush=True)
                elif t == "llm_token":
                    token = resp.get("payload", {}).get("token", "")
                    print(token, end="", flush=True)
                elif t == "audio_output":
                    audio_b64 = resp.get("payload", {}).get("data", "")
                    audio_bytes = base64.b64decode(audio_b64)
                    print(
                        f"\n\n✓ Audio received ({len(audio_bytes)} bytes), playing..."
                    )
                    play_audio(audio_bytes)
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
