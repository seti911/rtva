#!/usr/bin/env python3
"""Test TTS with streaming audio playback (starts immediately on first chunk)."""

import asyncio
import json
import base64
import websockets
import subprocess
import os
import wave
import tempfile

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


class StreamingAudioPlayer:
    """Play audio chunks as they arrive using a named pipe."""

    def __init__(self, sample_rate=24000):
        self.sample_rate = sample_rate
        self.player_process = None
        self.pipe_path = None
        self.pipe_file = None
        self.running = False
        self.temp_dir = tempfile.mkdtemp()

    def start(self):
        """Start the player with a named pipe."""
        self.running = True
        self.pipe_path = os.path.join(self.temp_dir, "audio_fifo")

        # Create named pipe
        os.mkfifo(self.pipe_path)

        # Start aplay reading from the named pipe in background
        self.player_process = subprocess.Popen(
            [
                "aplay",
                "-f",
                "S16_LE",
                "-r",
                str(self.sample_rate),
                "-c",
                "1",
                self.pipe_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Open the pipe for writing
        self.pipe_file = open(self.pipe_path, "wb", buffering=0)
        print("🎵 Starting audio playback...")

    def add_chunk(self, audio_bytes):
        """Add audio chunk to be played."""
        if self.running and self.pipe_file:
            try:
                self.pipe_file.write(audio_bytes)
            except BrokenPipeError:
                # aplay closed the pipe (e.g., error)
                self.running = False

    def finish(self):
        """Finish writing and wait for playback to complete."""
        if self.running:
            self.running = False

            # Close the pipe
            if self.pipe_file:
                try:
                    self.pipe_file.close()
                except:
                    pass

            # Wait for aplay to finish
            if self.player_process:
                try:
                    self.player_process.wait(timeout=60)
                    print("✓ Audio playback complete")
                except subprocess.TimeoutExpired:
                    print("⚠ Timeout waiting for audio playback")
                    self.player_process.kill()

            # Clean up
            try:
                if self.pipe_path and os.path.exists(self.pipe_path):
                    os.unlink(self.pipe_path)
                os.rmdir(self.temp_dir)
            except:
                pass


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
                        f"\n[Chunk {chunk_count}: {len(audio_bytes)} bytes]",
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
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    question = "Bonjour, comment allez-vous?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    asyncio.run(test_tts(question))
