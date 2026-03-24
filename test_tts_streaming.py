#!/usr/bin/env python3
"""Test TTS with streaming audio playback (starts immediately on first chunk)."""

import asyncio
import json
import base64
import websockets
import subprocess
import tempfile
import os
import wave
from threading import Thread
from queue import Queue

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


class StreamingAudioPlayer:
    """Play audio chunks as they arrive, without waiting for all chunks."""

    def __init__(self, sample_rate=24000):
        self.sample_rate = sample_rate
        self.queue = Queue()
        self.player_process = None
        self.temp_file = None
        self.running = False

    def start(self):
        """Start the player thread."""
        self.running = True
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.temp_path = self.temp_file.name

        # Create WAV file header
        self.wav_file = wave.open(self.temp_path, "wb")
        self.wav_file.setnchannels(1)  # Mono
        self.wav_file.setsampwidth(2)  # 16-bit
        self.wav_file.setframerate(self.sample_rate)

        # Start aplay in background
        self.player_process = subprocess.Popen(
            ["aplay", self.temp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("🎵 Starting audio playback...")

    def add_chunk(self, audio_bytes):
        """Add audio chunk to be written and played."""
        if self.running:
            self.wav_file.writeframes(audio_bytes)
            # Flush the underlying file descriptor, not the Wave_write object
            self.wav_file._file.flush()

    def finish(self):
        """Finish writing and wait for playback to complete."""
        if self.running:
            self.running = False
            self.wav_file.close()

            # Wait for aplay to finish
            if self.player_process:
                try:
                    self.player_process.wait(timeout=60)
                    print("✓ Audio playback complete")
                except subprocess.TimeoutExpired:
                    print("⚠ Timeout waiting for audio playback")
                    self.player_process.kill()

            # Clean up
            if self.temp_path and os.path.exists(self.temp_path):
                os.unlink(self.temp_path)


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
            player = StreamingAudioPlayer()
            chunk_count = 0
            total_bytes = 0

            async for msg in ws:
                resp = json.loads(msg)
                t = resp.get("type")

                if t == "llm_token":
                    token = resp.get("payload", {}).get("token", "")
                    print(token, end="", flush=True)

                elif t == "audio_output":
                    audio_b64 = resp.get("payload", {}).get("data", "")
                    audio_bytes = base64.b64decode(audio_b64)

                    chunk_count += 1
                    total_bytes += len(audio_bytes)

                    # Start player on first chunk
                    if chunk_count == 1:
                        player.start()

                    # Add chunk to player
                    player.add_chunk(audio_bytes)
                    print(
                        f"\n[Chunk {chunk_count}: {len(audio_bytes)} bytes - playing now...]",
                        end="",
                        flush=True,
                    )

                elif t == "status":
                    state = resp.get("payload", {}).get("state")
                    if state == "listening" and chunk_count > 0:
                        # Audio is done, exit loop
                        break

            # Wait for all audio to finish playing
            if chunk_count > 0:
                player.finish()
                print(f"\n✓ Total audio: {total_bytes} bytes ({chunk_count} chunks)")
            else:
                print("\n✗ No audio received")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys

    question = "Bonjour, comment allez-vous?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    asyncio.run(test_tts(question))
