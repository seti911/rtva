"""Shared audio data structures and utilities."""

import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioFormat:
    """Audio format specification."""

    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16

    @property
    def bytes_per_sample(self) -> int:
        return self.bit_depth // 8

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate * self.channels * self.bytes_per_sample


class AudioBuffer:
    """Ring buffer for audio data."""

    def __init__(self, max_size: int = 16000 * 2):
        self.buffer = np.zeros(max_size, dtype=np.int16)
        self.write_pos = 0
        self.read_pos = 0
        self.max_size = max_size

    def write(self, data: np.ndarray) -> None:
        """Write audio data to buffer."""
        available = self.max_size - self.write_pos + self.read_pos
        if len(data) > available:
            data = data[-available:]

        end_pos = self.write_pos + len(data)
        if end_pos <= self.max_size:
            self.buffer[self.write_pos : end_pos] = data
        else:
            first_part = self.max_size - self.write_pos
            self.buffer[self.write_pos :] = data[:first_part]
            self.buffer[: len(data) - first_part] = data[first_part:]

        self.write_pos = end_pos % self.max_size

    def read(self, num_samples: int) -> Optional[np.ndarray]:
        """Read audio data from buffer."""
        if self.available() < num_samples:
            return None

        start = self.read_pos
        end = (start + num_samples) % self.max_size

        if end > start:
            data = self.buffer[start:end].copy()
        else:
            data = np.concatenate(
                [self.buffer[start:].copy(), self.buffer[:end].copy()]
            )

        self.read_pos = end
        return data

    def available(self) -> int:
        """Get number of available samples."""
        if self.write_pos >= self.read_pos:
            return self.write_pos - self.read_pos
        return self.max_size - self.read_pos + self.write_pos

    def clear(self) -> None:
        """Clear the buffer."""
        self.read_pos = self.write_pos


def encode_pcm16(audio: np.ndarray) -> bytes:
    """Encode audio as PCM16 bytes."""
    return audio.astype(np.int16).tobytes()


def decode_pcm16(data: bytes, channels: int = 1) -> np.ndarray:
    """Decode PCM16 bytes to audio array."""
    audio = np.frombuffer(data, dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels)
    return audio


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio to target sample rate."""
    if orig_sr == target_sr:
        return audio

    ratio = target_sr / orig_sr
    new_length = int(len(audio) * ratio)

    indices = np.linspace(0, len(audio) - 1, new_length)
    return np.interp(indices, np.arange(len(audio)), audio).astype(audio.dtype)


def normalize(audio: np.ndarray, target_level: float = 0.9) -> np.ndarray:
    """Normalize audio to target level."""
    if len(audio) == 0:
        return audio

    max_val = np.abs(audio).max()
    if max_val == 0:
        return audio

    return (audio / max_val * target_level * np.iinfo(np.int16).max).astype(np.int16)


def detect_silence(audio: np.ndarray, threshold: float = 500.0) -> bool:
    """Detect if audio segment is silence."""
    if len(audio) == 0:
        return True

    rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
    return rms < threshold


def calculate_rms(audio: np.ndarray) -> float:
    """Calculate RMS of audio segment."""
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
