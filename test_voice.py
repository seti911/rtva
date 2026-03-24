#!/usr/bin/env python3
"""Simple CLI client to test the voice assistant."""

import asyncio
import json
import websockets

URI = "ws://localhost:8000/ws"


async def listen_loop():
    async with websockets.connect(URI) as ws:
        print("Connected! Sending listen_start...")
        await ws.send(json.dumps({"type": "listen_start"}))

        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                print(f"← {json.dumps(data, indent=2)}")

                if data.get("type") == "audio_output":
                    print("🎤 Audio response received!")
        except asyncio.TimeoutError:
            print("No more messages, stopping...")
            await ws.send(json.dumps({"type": "listen_stop"}))


if __name__ == "__main__":
    print("Starting voice assistant test...")
    print("Speak into microphone - the assistant should respond.")
    print("Press Ctrl+C to stop.\n")
    asyncio.run(listen_loop())
