#!/usr/bin/env python3
"""Full pipeline test: Mic → STT → Orchestrator → LLM → TTS → Speaker."""

import asyncio
import json
import base64
import pyaudio
import websockets
import numpy as np
import sys

STT_URL = "ws://localhost:8001/stt"
ORCHESTRATOR_URL = "ws://localhost:8000/ws"
CHUNK_SIZE = 2048


def play_audio(audio_bytes: bytes):
    """Play raw PCM audio."""
    audio = np.frombuffer(audio_bytes, dtype=np.int16)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    stream.write(audio.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()


async def full_pipeline():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=10,
    )

    print("Say something into mic (speak now)...")

    # Get transcription
    stt_ws = await websockets.connect(STT_URL)
    await stt_ws.send(json.dumps({"type": "start", "payload": {"language": "fr"}}))

    transcription = ""
    for i in range(100):
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        audio_b64 = base64.b64encode(data).decode()
        await stt_ws.send(
            json.dumps({"type": "audio", "payload": {"pcm_data": audio_b64}})
        )

        try:
            msg = await asyncio.wait_for(stt_ws.recv(), timeout=0.1)
            resp = json.loads(msg)
            text = resp.get("payload", {}).get("text", "")

            # Accept any transcription with reasonable audio level
            if text and len(text) > 3:
                transcription = text
                print(f"Got: {text}")
        except:
            pass

    await stt_ws.send(json.dumps({"type": "stop"}))
    await stt_ws.close()
    stream.close()
    p.terminate()

    if not transcription:
        print("No speech detected, try again")
        return

    print(f"Transcription: {transcription}")

    # Send to orchestrator
    ws = await websockets.connect(ORCHESTRATOR_URL)
    await ws.send(json.dumps({"type": "listen_start"}))
    await ws.recv()

    await ws.send(
        json.dumps(
            {
                "type": "transcription",
                "payload": {"text": transcription, "is_final": True},
            }
        )
    )
    print("Waiting for response...")

    # Wait for audio
    async for msg in ws:
        resp = json.loads(msg)
        t = resp.get("type")

        if t == "status":
            print(f"State: {resp.get('payload', {}).get('state')}")
        elif t == "audio_output":
            audio_b64 = resp.get("payload", {}).get("data", "")
            print(f"Playing {len(audio_b64)} bytes...")
            audio_bytes = base64.b64decode(audio_b64)
            play_audio(audio_bytes)
            print("Done!")
            break

    await ws.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Voice Assistant - Full Pipeline Test")
    print("=" * 50)
    try:
        asyncio.run(full_pipeline())
    except KeyboardInterrupt:
        print("\nStopped")
