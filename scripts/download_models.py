#!/usr/bin/env python3
"""Download models for the voice assistant."""

import os
import sys


def download_whisper():
    """Download Whisper model."""
    print("Downloading Whisper model...")
    from faster_whisper import WhisperModel

    # Try CUDA first, fallback to CPU
    try:
        model = WhisperModel("small", device="cuda", compute_type="int8_float16")
        print("Whisper model downloaded (CUDA)")
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("CUDA OOM, downloading CPU version...")
            model = WhisperModel("small", device="cpu", compute_type="int8")
            print("Whisper model downloaded (CPU)")
        else:
            raise


def download_mistral():
    """Download Mistral 7B GGUF model."""
    print("\nDownloading Mistral 7B model...")
    print("Please manually download from:")
    print("  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
    print("\nPlace the file as: models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf")

    # Check if already exists
    mistral_path = "models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    if os.path.exists(mistral_path):
        print(f"Mistral model already exists at {mistral_path}")
    else:
        print(f"Mistral model not found at {mistral_path}")


def download_xtts():
    """Download XTTS model."""
    print("\nXTTS model will be downloaded automatically on first use.")
    print("Or manually from: https://huggingface.co/coqui/XTTS-v2")


if __name__ == "__main__":
    os.makedirs("models/whisper", exist_ok=True)
    os.makedirs("models/mistral", exist_ok=True)
    os.makedirs("models/xtts", exist_ok=True)

    download_whisper()
    download_mistral()
    download_xtts()

    print("\n=== Model Setup Complete ===")
    print("Next steps:")
    print("1. Download Mistral GGUF model manually")
    print("2. Run: docker compose up -d")
