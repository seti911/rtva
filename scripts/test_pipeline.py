#!/usr/bin/env python3
"""Test script for the voice assistant pipeline."""

import asyncio
import json
import websockets


async def test_pipeline():
    """Test the complete pipeline."""

    print("Testing voice assistant pipeline...")

    # Connect to orchestrator
    uri = "ws://localhost:8000"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")

        # Send listen start
        await websocket.send(json.dumps({"type": "listen_start"}))
        print("Sent: listen_start")

        # Wait for status
        response = await websocket.recv()
        print(f"Received: {response}")

        # Send a test transcription
        await websocket.send(
            json.dumps(
                {
                    "type": "transcription",
                    "payload": {"text": "Bonjour, comment ça va?", "is_final": True},
                }
            )
        )
        print("Sent: test transcription")

        # Receive responses
        for i in range(10):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(
                    f"Received [{i}]: {response[:200]}..."
                    if len(response) > 200
                    else f"Received [{i}]: {response}"
                )
            except asyncio.TimeoutError:
                break

    print("Pipeline test complete!")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
