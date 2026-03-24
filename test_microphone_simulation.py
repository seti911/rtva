#!/usr/bin/env python3
"""Test microphone client with simulated audio input (no actual mic needed)."""

import asyncio
import sys
import os

# Add the repo to path
sys.path.insert(0, "/home/stef/Development/localAI/rtva")

from microphone_client import MicrophoneVoiceAssistant


class SimulatedMicrophoneAssistant(MicrophoneVoiceAssistant):
    """Assistant with simulated microphone input for testing."""

    def capture_microphone(self, duration: float = 5.0) -> bytes:
        """Use test WAV file instead of actual microphone."""
        print(f"🎤 Using simulated microphone (loading test audio)...")

        # Load test audio file
        test_audio_path = (
            "/home/stef/Development/localAI/rtva/models/parakeet/test_wavs/fr.wav"
        )
        with open(test_audio_path, "rb") as f:
            wav_data = f.read()

        # Skip WAV header (44 bytes)
        pcm_data = wav_data[44:]
        print(f"  ✓ Loaded {len(pcm_data)} bytes from test file")
        return pcm_data


async def main():
    """Test with simulated microphone."""
    print("=" * 70)
    print("MICROPHONE SIMULATION TEST")
    print("=" * 70)
    print("\nThis test uses pre-recorded French audio instead of actual mic.")
    print("It will simulate 2 conversation turns.\n")

    assistant = SimulatedMicrophoneAssistant()

    # Run 2 turns of the conversation
    await assistant.run(recording_duration=5.0, num_turns=2)


if __name__ == "__main__":
    asyncio.run(main())
