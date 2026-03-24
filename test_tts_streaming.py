#!/usr/bin/env python3
"""Test TTS with streaming audio playback (starts immediately on first chunk)."""

import asyncio
import json
import base64
import websockets
import subprocess
import os
import tempfile
import struct

ORCHESTRATOR_URL = "ws://localhost:8000/ws"


class StreamingAudioPlayer:
    """Play audio chunks as they arrive using ffmpeg (smooth streaming)."""

    def __init__(self, sample_rate=24000):
        self.sample_rate = sample_rate
        self.player_process = None
        self.pipe_path = None
        self.pipe_file = None
        self.running = False
        self.temp_dir = tempfile.mkdtemp()
        self.total_samples = 0

    def start(self):
        """Start ffmpeg to play raw PCM from a named pipe."""
        self.running = True
        self.pipe_path = os.path.join(self.temp_dir, "audio_fifo")

        # Create named pipe
        try:
            os.mkfifo(self.pipe_path)
        except FileExistsError:
            os.unlink(self.pipe_path)
            os.mkfifo(self.pipe_path)

        # Start ffmpeg reading raw PCM and piping to aplay
        # ffmpeg will handle the audio format conversion smoothly
        self.player_process = subprocess.Popen(
            [
                "ffmpeg",
                "-f",
                "s16le",  # Input: signed 16-bit little-endian
                "-ar",
                str(self.sample_rate),  # Sample rate
                "-ac",
                "1",  # Mono
                "-i",
                self.pipe_path,  # Read from FIFO
                "-f",
                "s16le",  # Output format
                "-",  # Output to stdout
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

        # Pipe ffmpeg output to aplay
        self.aplay_process = subprocess.Popen(
            ["aplay", "-f", "S16_LE", "-r", str(self.sample_rate), "-c", "1"],
            stdin=self.player_process.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Allow ffmpeg's stdout to be used by aplay
        self.player_process.stdout.close()

        # Open the pipe for writing
        self.pipe_file = open(self.pipe_path, "wb", buffering=0)
        print("🎵 Starting audio playback...")

    def add_chunk(self, audio_bytes):
        """Add audio chunk to be played."""
        if self.running and self.pipe_file:
            try:
                self.pipe_file.write(audio_bytes)
                self.pipe_file.flush()
                self.total_samples += (
                    len(audio_bytes) // 2
                )  # 16-bit = 2 bytes per sample
            except (BrokenPipeError, OSError):
                # aplay/ffmpeg closed the pipe
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

            # Wait for processes to finish
            if self.aplay_process:
                try:
                    self.aplay_process.wait(timeout=60)
                    print("✓ Audio playback complete")
                except subprocess.TimeoutExpired:
                    print("⚠ Timeout waiting for audio playback")
                    self.aplay_process.kill()

            if self.player_process:
                try:
                    self.player_process.wait(timeout=5)
                except:
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
                    duration_ms = (len(audio_bytes) // 2 / 24000) * 1000
                    print(
                        f"\n[Chunk {chunk_count}: {len(audio_bytes)} bytes (~{duration_ms:.0f}ms)]",
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
                total_duration = total_bytes // 2 / 24000
                print(
                    f"\n✓ Total audio: {total_bytes} bytes ({chunk_count} chunks, ~{total_duration:.1f}s)"
                )
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
