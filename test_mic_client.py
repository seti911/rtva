#!/usr/bin/env python3
"""Audio client that captures mic and sends directly to STT service."""

import asyncio
import json
import base64
import pyaudio
import websockets
import sys

STT_URL = "ws://localhost:8001/stt"
ORCHESTRATOR_URL = "ws://localhost:8000/ws"
CHUNK_SIZE = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


async def audio_to_stt():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=7,  # USB Microphone
    )

    print("Microphone opened. Say something...", flush=True)

    # Connect to orchestrator to start listening state
    async with websockets.connect(ORCHESTRATOR_URL) as orch:
        await orch.send(json.dumps({"type": "listen_start"}))
        print("Orchestrator: listen_start sent", flush=True)

    # Connect to STT and stream audio
    async with websockets.connect(STT_URL) as stt_ws:
        # Send start command to STT
        await stt_ws.send(json.dumps({"type": "start", "payload": {"language": "fr"}}))
        print("STT: start sent", flush=True)

        # Stream audio chunks
        chunk_count = 0
        for chunk_count in range(100):  # ~6-7 seconds
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_b64 = base64.b64encode(data).decode()

            await stt_ws.send(
                json.dumps({"type": "audio", "payload": {"pcm_data": audio_b64}})
            )

            # Try to receive transcription
            try:
                msg = await asyncio.wait_for(stt_ws.recv(), timeout=0.5)
                print(f"STT: {msg[:100]}...", flush=True)
            except asyncio.TimeoutError:
                print(".", end="", flush=True)

        print("\nSending stop...", flush=True)
        # Send stop
        await stt_ws.send(json.dumps({"type": "stop"}))
        print("STT: stop sent", flush=True)

        # Wait for final transcription
        try:
            msg = await asyncio.wait_for(stt_ws.recv(), timeout=10)
            print(f"Final: {msg}", flush=True)
        except Exception as e:
            print(f"No final response: {e}", flush=True)

    print("Done", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(audio_to_stt())
    except KeyboardInterrupt:
        print("\nStopped", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
