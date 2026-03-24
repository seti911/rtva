#!/usr/bin/env python3
"""Microphone voice assistant - Captures audio and runs full STT → LLM → TTS → Audio pipeline."""

import asyncio
import base64
import json
import websockets
import numpy as np
import time
import sys

# Try to import audio libraries
try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠ pyaudio not available, will try sounddevice")

try:
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠ sounddevice not available")


class MicrophoneVoiceAssistant:
    """Microphone-based voice assistant using the full pipeline."""

    def __init__(
        self,
        stt_url: str = "ws://localhost:8001/stt",
        llm_url: str = "ws://localhost:8002/llm",
        tts_url: str = "ws://localhost:8003/tts",
        sample_rate: int = 16000,
        chunk_size: int = 4096,
    ):
        self.stt_url = stt_url
        self.llm_url = llm_url
        self.tts_url = tts_url
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_buffer = []

    def capture_microphone(self, duration: float = 5.0) -> bytes:
        """Capture audio from microphone for specified duration."""
        print(f"🎤 Listening for {duration:.1f} seconds...")

        if SOUNDDEVICE_AVAILABLE:
            return self._capture_with_sounddevice(duration)
        elif PYAUDIO_AVAILABLE:
            return self._capture_with_pyaudio(duration)
        else:
            print("✗ Neither pyaudio nor sounddevice available!")
            print("Install with: pip install sounddevice")
            return b""

    def _capture_with_sounddevice(self, duration: float) -> bytes:
        """Capture audio using sounddevice library."""
        try:
            print(f"  Using sounddevice (sample_rate={self.sample_rate})")
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,
            )
            sd.wait()  # Wait until recording is finished

            # Convert to bytes
            audio_bytes = recording.tobytes()
            print(f"  ✓ Recorded {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            print(f"  ✗ Error with sounddevice: {e}")
            return b""

    def _capture_with_pyaudio(self, duration: float) -> bytes:
        """Capture audio using pyaudio library."""
        try:
            print(f"  Using pyaudio (sample_rate={self.sample_rate})")
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            frames = []
            num_frames = int(duration * self.sample_rate / self.chunk_size)

            for _ in range(num_frames):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            pa.terminate()

            audio_bytes = b"".join(frames)
            print(f"  ✓ Recorded {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            print(f"  ✗ Error with pyaudio: {e}")
            return b""

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Send audio to STT service and get transcription."""
        print("\n📝 Sending to STT service...")
        try:
            async with websockets.connect(self.stt_url, ping_interval=None) as ws:
                payload = {
                    "type": "audio",
                    "payload": {
                        "pcm_data": base64.b64encode(audio_bytes).decode("utf-8"),
                        "sample_rate": self.sample_rate,
                    },
                }

                await ws.send(json.dumps(payload))
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                result = json.loads(response)

                text = result["payload"]["text"]
                print(f'  ✓ You said: "{text}"')
                return text

        except Exception as e:
            print(f"  ✗ STT error: {e}")
            return ""

    async def generate_response(self, user_text: str) -> str:
        """Send user text to LLM and get AI response."""
        print("\n🧠 Thinking...")
        try:
            async with websockets.connect(self.llm_url, ping_interval=None) as ws:
                prompt = f"[INST] You are a helpful French assistant. Respond briefly in French. {user_text} [/INST]"

                payload = {
                    "type": "generate",
                    "payload": {
                        "prompt": prompt,
                        "max_tokens": 100,
                    },
                }

                await ws.send(json.dumps(payload))

                # Collect tokens
                tokens = []
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    result = json.loads(response)

                    if result.get("type") == "token":
                        token = result["payload"].get("token", "")
                        tokens.append(token)
                    elif result.get("type") == "done":
                        break

                ai_response = "".join(tokens).strip()
                print(f'  ✓ AI said: "{ai_response}"')
                return ai_response

        except Exception as e:
            print(f"  ✗ LLM error: {e}")
            return ""

    async def synthesize_speech(self, text: str) -> bytes:
        """Send text to TTS service and get audio."""
        print("\n🔊 Synthesizing speech...")
        try:
            async with websockets.connect(self.tts_url, ping_interval=None) as ws:
                payload = {
                    "type": "synthesize",
                    "payload": {
                        "text": text,
                        "language": "fr",
                    },
                }

                await ws.send(json.dumps(payload))

                # Collect audio chunks
                audio_chunks = []
                try:
                    while True:
                        response = await asyncio.wait_for(ws.recv(), timeout=30)
                        result = json.loads(response)

                        if result.get("type") == "audio":
                            chunk_data = result["payload"].get("audio_data")
                            if chunk_data:
                                audio_chunks.append(base64.b64decode(chunk_data))
                            if result["payload"].get("is_final"):
                                break
                        elif result.get("type") == "end":
                            break
                except asyncio.TimeoutError:
                    pass

                audio_bytes = b"".join(audio_chunks)
                print(f"  ✓ Generated {len(audio_bytes)} bytes of audio")
                return audio_bytes

        except Exception as e:
            print(f"  ✗ TTS error: {e}")
            return b""

    def play_audio(self, audio_bytes: bytes) -> None:
        """Play audio using sounddevice or pyaudio."""
        if not audio_bytes:
            print("  ⚠ No audio to play")
            return

        print("🎵 Playing response...")

        try:
            if SOUNDDEVICE_AVAILABLE:
                # Convert bytes to numpy array
                audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0

                sd.play(audio_float32, samplerate=24000)
                sd.wait()
                print("  ✓ Done!")
                return
        except Exception as e:
            print(f"  ⚠ Could not play with sounddevice: {e}")

        # Fallback to file-based playback
        try:
            import subprocess

            with open("/tmp/response_audio.wav", "wb") as f:
                # Write WAV header
                import struct

                sample_rate = 24000
                sample_width = 2
                channels = 1
                frame_count = len(audio_bytes) // sample_width

                f.write(b"RIFF")
                f.write(struct.pack("<I", 36 + len(audio_bytes)))
                f.write(b"WAVE")
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
                f.write(b"data")
                f.write(struct.pack("<I", len(audio_bytes)))
                f.write(audio_bytes)

            subprocess.run(["aplay", "/tmp/response_audio.wav"], check=True)
            print("  ✓ Done!")
        except Exception as e:
            print(f"  ⚠ Could not play audio: {e}")

    async def run(self, recording_duration: float = 5.0, num_turns: int = -1):
        """Run the voice assistant loop."""
        print("=" * 70)
        print("FRENCH VOICE ASSISTANT - Microphone Client")
        print("=" * 70)
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Recording duration: {recording_duration:.1f} seconds per turn")
        print("Press Ctrl+C to exit\n")

        turn = 0
        while num_turns < 0 or turn < num_turns:
            turn += 1
            print(f"\n{'─' * 70}")
            print(f"TURN {turn}")
            print(f"{'─' * 70}")

            try:
                # Step 1: Capture audio
                audio_bytes = await asyncio.to_thread(
                    self.capture_microphone, recording_duration
                )
                if not audio_bytes:
                    print("✗ Failed to capture audio")
                    continue

                # Step 2: Transcribe
                user_text = await self.transcribe_audio(audio_bytes)
                if not user_text:
                    print("✗ Failed to transcribe")
                    continue

                # Step 3: Generate response
                ai_response = await self.generate_response(user_text)
                if not ai_response:
                    print("✗ Failed to generate response")
                    continue

                # Step 4: Synthesize speech
                response_audio = await self.synthesize_speech(ai_response)
                if not response_audio:
                    print("✗ Failed to synthesize speech")
                    continue

                # Step 5: Play audio
                await asyncio.to_thread(self.play_audio, response_audio)

            except KeyboardInterrupt:
                print("\n\n✓ Exiting...")
                break
            except Exception as e:
                print(f"\n✗ Error in turn {turn}: {e}")
                import traceback

                traceback.print_exc()

        print("\n" + "=" * 70)
        print("Voice assistant session ended")
        print("=" * 70)


async def main():
    """Main entry point."""
    # Check if microphone library is available
    if not (SOUNDDEVICE_AVAILABLE or PYAUDIO_AVAILABLE):
        print("ERROR: Neither sounddevice nor pyaudio is installed!")
        print("\nInstall one of them:")
        print("  pip install sounddevice")
        print("  OR")
        print("  pip install pyaudio")
        sys.exit(1)

    assistant = MicrophoneVoiceAssistant()
    await assistant.run(recording_duration=5.0, num_turns=-1)


if __name__ == "__main__":
    asyncio.run(main())
