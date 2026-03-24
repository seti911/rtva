#!/usr/bin/env python3
"""Test TTS by sending a text query to the LLM via orchestrator."""

import asyncio
import json
import sys
import base64
import websockets
import numpy as np
import pyaudio

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


def play_audio(audio_bytes: bytes):
    """Play raw PCM audio."""
    audio = np.frombuffer(audio_bytes, dtype=np.int16)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    stream.write(audio.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()


async def test_tts(question: str):
    print(f"Connecting to {ORCHESTRATOR_URL}...")
    async with websockets.connect(ORCHESTRATOR_URL) as ws:
        print("Connected! Starting listen_start...")
        await ws.send(json.dumps({"type": "listen_start"}))
        await ws.recv()

        print(f"Sending question: {question}")
        await ws.send(
            json.dumps(
                {
                    "type": "transcription",
                    "payload": {"text": question, "is_final": True},
                }
            )
        )

        print("Waiting for audio response...\n")
        async for msg in ws:
            resp = json.loads(msg)
            t = resp.get("type")

            if t == "status":
                print(f"[Status] state={resp.get('payload', {}).get('state')}")
            elif t == "llm_token":
                token = resp.get("payload", {}).get("token", "")
                print(token, end="", flush=True)
            elif t == "audio_output":
                audio_b64 = resp.get("payload", {}).get("data", "")
                print(f"\n[Audio] {len(audio_b64)} bytes, playing...")
                audio_bytes = base64.b64decode(audio_b64)
                play_audio(audio_bytes)
            elif t == "done":
                print("\n[Done]")
                break


if __name__ == "__main__":
    question = "Qu'est-ce que tu peux faire ?"  # "What can you do?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    asyncio.run(test_tts(question))
