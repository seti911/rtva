#!/usr/bin/env python3
"""End-to-end pipeline test: STT → LLM → TTS → Audio Playback."""

import asyncio
import base64
import json
import websockets
import subprocess
import time
import os


async def test_full_pipeline():
    """Test the complete pipeline."""

    # Read test audio
    with open(
        "/home/stef/Development/localAI/rtva/models/parakeet/test_wavs/fr.wav", "rb"
    ) as f:
        pcm_data = f.read()[44:]

    print("=" * 60)
    print("FULL PIPELINE TEST: STT → LLM → TTS → Audio")
    print("=" * 60)

    # Step 1: STT (Speech-to-Text)
    print("\n[1/4] Testing STT Service...")
    try:
        async with websockets.connect(
            "ws://localhost:8001/stt", ping_interval=None
        ) as ws:
            payload = {
                "type": "audio",
                "payload": {
                    "pcm_data": base64.b64encode(pcm_data).decode("utf-8"),
                    "sample_rate": 22050,
                },
            }

            await ws.send(json.dumps(payload))
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            result = json.loads(response)
            user_text = result["payload"]["text"]
            print(f'   ✓ User said: "{user_text}"')
    except Exception as e:
        print(f"   ✗ STT failed: {e}")
        return

    # Step 2: LLM (Language Model)
    print("\n[2/4] Testing LLM Service...")
    try:
        async with websockets.connect(
            "ws://localhost:8002/llm", ping_interval=None
        ) as ws:
            # Format: [INST] {system_message} {user_message} [/INST]
            prompt = f"[INST] You are a helpful French assistant. Respond briefly in French. {user_text} [/INST]"

            payload = {
                "type": "generate",
                "payload": {
                    "prompt": prompt,
                    "max_tokens": 100,
                },
            }

            await ws.send(json.dumps(payload))

            # Collect all tokens until "done" message
            tokens = []
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    result = json.loads(response)
                    msg_type = result.get("type")

                    if msg_type == "token":
                        token = result["payload"].get("token", "")
                        tokens.append(token)
                    elif msg_type == "done":
                        break
                    elif msg_type == "error":
                        raise Exception(
                            result["payload"].get("message", "Unknown error")
                        )
            except asyncio.TimeoutError:
                pass

            llm_response = "".join(tokens).strip()
            print(f'   ✓ LLM said: "{llm_response}"')
    except Exception as e:
        print(f"   ✗ LLM failed: {e}")
        return

    # Step 3: TTS (Text-to-Speech)
    print("\n[3/4] Testing TTS Service...")
    try:
        # Request TTS through websocket with streaming
        async with websockets.connect(
            "ws://localhost:8003/tts", ping_interval=None
        ) as ws:
            payload = {
                "type": "synthesize",
                "payload": {
                    "text": llm_response,
                    "language": "fr",
                },
            }

            await ws.send(json.dumps(payload))

            # Collect all audio chunks
            audio_chunks = []
            chunk_count = 0
            start_time = time.time()

            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    result = json.loads(response)
                    msg_type = result.get("type")

                    if msg_type == "audio" or msg_type == "audio_chunk":
                        chunk_data = result["payload"].get("audio_data")
                        if chunk_data:
                            audio_chunks.append(base64.b64decode(chunk_data))
                            chunk_count += 1
                        # If it's a single "audio" message with is_final, stop
                        if msg_type == "audio" and result["payload"].get("is_final"):
                            break
                    elif msg_type == "end":
                        break
                    elif msg_type == "error":
                        print(
                            f"   ⚠ TTS error: {result['payload'].get('message', 'Unknown')}"
                        )
                        break
            except asyncio.TimeoutError:
                pass

            elapsed = time.time() - start_time
            total_audio_bytes = sum(len(chunk) for chunk in audio_chunks)
            print(
                f"   ✓ Received {chunk_count} audio chunks ({total_audio_bytes} bytes) in {elapsed:.2f}s"
            )

            # Save audio to file
            output_path = "/tmp/tts_output.wav"
            with open(output_path, "wb") as f:
                # Write simple WAV header (mono, 24kHz, 16-bit)
                import struct

                sample_rate = 24000
                sample_width = 2
                channels = 1

                # Combine all audio chunks
                audio_data = b"".join(audio_chunks)
                frame_count = len(audio_data) // sample_width

                # RIFF header
                f.write(b"RIFF")
                f.write(struct.pack("<I", 36 + len(audio_data)))
                f.write(b"WAVE")

                # fmt sub-chunk
                f.write(b"fmt ")
                f.write(struct.pack("<I", 16))
                f.write(
                    struct.pack(
                        "<HHIIHH",
                        1,
                        channels,
                        sample_rate,
                        sample_rate * channels * sample_width,
                        channels * sample_width,
                        16,
                    )
                )

                # data sub-chunk
                f.write(b"data")
                f.write(struct.pack("<I", len(audio_data)))
                f.write(audio_data)

            print(f"   ✓ Saved audio to {output_path}")

    except Exception as e:
        print(f"   ✗ TTS failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 4: Audio Playback
    print("\n[4/4] Playing audio...")
    try:
        # Try to play with aplay
        if os.path.exists("/tmp/tts_output.wav"):
            result = subprocess.run(
                ["aplay", "/tmp/tts_output.wav"], capture_output=True, timeout=30
            )
            print(f"   ✓ Audio played successfully")
        else:
            print(f"   ⚠ Audio file not found")
    except FileNotFoundError:
        print(f"   ⚠ aplay not available, skipping playback")
    except Exception as e:
        print(f"   ⚠ Could not play audio: {e}")

    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
