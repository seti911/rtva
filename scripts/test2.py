#!/usr/bin/env python3
"""Simple test for the voice assistant pipeline."""

import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8000"

    async with websockets.connect(uri) as ws:
        # Start listening
        await ws.send(json.dumps({"type": "listen_start"}))
        resp = await ws.recv()
        print(f"Status: {resp}")

        # Send transcription
        await ws.send(
            json.dumps(
                {
                    "type": "transcription",
                    "payload": {"text": "Bonjour", "is_final": True},
                }
            )
        )

        # Collect responses
        try:
            while True:
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                print(f"Got: {resp[:100]}...")
        except asyncio.TimeoutError:
            print("Done waiting")
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(test())
