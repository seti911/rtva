#!/usr/bin/env python3
"""Test pipeline with simple input."""

import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8000"

    async with websockets.connect(uri) as ws:
        # Send a simple transcription
        await ws.send(
            json.dumps(
                {
                    "type": "transcription",
                    "payload": {"text": "Salut", "is_final": True},
                }
            )
        )

        try:
            for i in range(10):
                resp = await asyncio.wait_for(ws.recv(), timeout=30.0)
                data = json.loads(resp)
                print(f"[{i}] {data.get('type')}")
                if data.get("type") == "audio_output":
                    payload = data.get("payload", {})
                    print(
                        f"    Audio: {len(payload.get('data', ''))} bytes, {payload.get('duration_ms')}ms"
                    )
        except Exception as e:
            print(f"Done: {e}")


asyncio.run(test())
