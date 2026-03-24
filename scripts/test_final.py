#!/usr/bin/env python3
"""Test pipeline with full flow."""

import asyncio
import json
import websockets
import base64


async def test():
    uri = "ws://localhost:8000"

    async with websockets.connect(uri) as ws:
        # Send a simple transcription
        await ws.send(
            json.dumps(
                {
                    "type": "transcription",
                    "payload": {"text": "Dis bonjour", "is_final": True},
                }
            )
        )

        print("Sent: Dis bonjour")

        try:
            for i in range(15):
                resp = await asyncio.wait_for(ws.recv(), timeout=30.0)
                data = json.loads(resp)
                msg_type = data.get("type")
                print(f"[{i}] {msg_type}")

                if msg_type == "audio_output":
                    payload = data.get("payload", {})
                    audio_data = payload.get("data", "")
                    if audio_data:
                        audio_bytes = base64.b64decode(audio_data)
                        print(
                            f"    Audio: {len(audio_bytes)} bytes, {payload.get('duration_ms')}ms"
                        )

        except Exception as e:
            print(f"Done: {e}")


asyncio.run(test())
