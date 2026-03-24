#!/usr/bin/env python3
"""Test STT service with audio sample."""

import asyncio
import base64
import json
import websockets

async def test_stt():
    """Test STT with a real audio file."""
    # Read French test audio
    audio_path = "/home/stef/Development/localAI/rtva/models/parakeet/test_wavs/fr.wav"
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    print(f"Loaded audio: {len(audio_data)} bytes")
    
    # Skip WAV header (44 bytes) to get PCM data
    pcm_data = audio_data[44:]
    print(f"PCM data: {len(pcm_data)} bytes")
    
    # Connect to STT service
    uri = "ws://localhost:8001/stt"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected!")
            
            # Send audio data
            payload = {
                "type": "audio",
                "payload": {
                    "pcm_data": base64.b64encode(pcm_data).decode("utf-8")
                }
            }
            
            message = json.dumps(payload)
            print(f"Sending audio ({len(message)} bytes)...")
            await websocket.send(message)
            
            # Wait for response
            print("Waiting for transcription...")
            response = await websocket.recv()
            print(f"Response: {response}")
            
            # Parse response
            result = json.loads(response)
            print(f"\n✓ Transcription: {result}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stt())
