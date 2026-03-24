#!/usr/bin/env python3
"""Test TTS and play audio using aplay (more reliable)."""

import asyncio
import json
import base64
import websockets
import subprocess
import tempfile
import os

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


async def test_tts(question: str):
    print(f"Connecting to {ORCHESTRATOR_URL}...")
    try:
        async with websockets.connect(ORCHESTRATOR_URL) as ws:
            print("✓ Connected")

            await ws.send(json.dumps({"type": "listen_start"}))
            msg = await ws.recv()
            print(f"✓ Listen started")

            print(f'\nSending question: "{question}"')
            await ws.send(
                json.dumps(
                    {
                        "type": "transcription",
                        "payload": {"text": question, "is_final": True},
                    }
                )
            )

            print("\nLLM Response:")
            audio_received = False
            audio_chunks = []
            async for msg in ws:
                resp = json.loads(msg)
                t = resp.get("type")

                if t == "llm_token":
                    token = resp.get("payload", {}).get("token", "")
                    print(token, end="", flush=True)
                elif t == "audio_output":
                    audio_b64 = resp.get("payload", {}).get("data", "")
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_chunks.append(audio_bytes)
                    print(
                        f"\n[Audio chunk: {len(audio_bytes)} bytes]", end="", flush=True
                    )
                    audio_received = True
                elif t == "status":
                    state = resp.get("payload", {}).get("state")
                    if state == "listening":
                        # All done, play collected audio
                        break

            if audio_received and audio_chunks:
                total_bytes = sum(len(chunk) for chunk in audio_chunks)
                print(
                    f"\n\n✓ Total audio received: {total_bytes} bytes ({len(audio_chunks)} chunks)"
                )

                # Concatenate all chunks
                full_audio = b"".join(audio_chunks)

                # Save to temporary file and play with aplay
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                    # Write WAV header for 24kHz mono 16-bit
                    import wave

                    with wave.open(temp_path, "wb") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(24000)
                        wav.writeframes(full_audio)

                print(f"Playing complete audio from {temp_path}...")
                try:
                    subprocess.run(["aplay", temp_path], check=True, timeout=60)
                    print("✓ Audio playback complete")
                except subprocess.TimeoutExpired:
                    print("Timeout during playback")
                except Exception as e:
                    print(f"Error during playback: {e}")
                finally:
                    os.unlink(temp_path)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys

    question = "Bonjour, comment allez-vous?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    asyncio.run(test_tts(question))
