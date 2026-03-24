#!/usr/bin/env python3
"""Test TTS directly."""

import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8003/tts"

    async with websockets.connect(uri) as ws:
        await ws.send(
            json.dumps(
                {
                    "type": "synthesize",
                    "payload": {
                        "text": "Bonjour, comment allez-vous?",
                        "language": "fr",
                    },
                }
            )
        )

        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=30.0)
            print(f"Response: {resp[:200]}...")
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(test())
