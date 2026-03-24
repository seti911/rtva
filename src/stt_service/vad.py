"""Voice Activity Detection (VAD) module."""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""

    sample_rate: int = 16000
    frame_duration_ms: int = 30
    speech_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 300
    silence_threshold: float = 0.1


class VoiceActivityDetector:
    """Simple energy-based voice activity detector."""

    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self.frame_size = int(
            self.config.sample_rate * self.config.frame_duration_ms / 1000
        )
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0

    def detect(self, audio: np.ndarray) -> bool:
        """
        Detect if audio frame contains speech.

        Args:
            audio: Audio samples as numpy array

        Returns:
            True if speech detected, False otherwise
        """
        if len(audio) < self.frame_size:
            audio = np.pad(audio, (0, self.frame_size - len(audio)))

        energy = self._calculate_energy(audio)

        is_speech = energy > self.config.speech_threshold

        if is_speech:
            self.speech_frames += 1
            self.silence_frames = 0
        else:
            self.silence_frames += 1

        min_speech_frames = int(
            self.config.min_speech_duration_ms / self.config.frame_duration_ms
        )
        min_silence_frames = int(
            self.config.min_silence_duration_ms / self.config.frame_duration_ms
        )

        if (
            is_speech
            and not self.is_speaking
            and self.speech_frames >= min_speech_frames
        ):
            self.is_speaking = True
            return True

        if (
            not is_speech
            and self.is_speaking
            and self.silence_frames >= min_silence_frames
        ):
            self.is_speaking = False
            self.speech_frames = 0
            return False

        return self.is_speaking

    def _calculate_energy(self, audio: np.ndarray) -> float:
        """Calculate root mean square energy of audio frame."""
        if len(audio) == 0:
            return 0.0

        audio_float = audio.astype(np.float32) / np.iinfo(np.int16).max
        energy = np.sqrt(np.mean(audio_float**2))

        return min(energy * 10, 1.0)

    def reset(self) -> None:
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0


class SileroVAD:
    """Silero VAD wrapper for better voice detection."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self._model_loaded = False

    async def load_model(self) -> None:
        """Load Silero VAD model."""
        try:
            import torch
            import urllib.request

            if self.model_path:
                self.model = torch.jit.load(self.model_path)
            else:
                model_url = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.jit"
                torch.hub.set_dir("/tmp/torch")
                self.model, _ = torch.hub.load(
                    "snakers4/silero-vad", "silero_vad", force_reload=False
                )

            self._model_loaded = True
        except Exception as e:
            print(f"Failed to load Silero VAD: {e}")
            self._model_loaded = False

    def detect(self, audio: np.ndarray, sample_rate: int = 16000) -> float:
        """
        Get voice probability.

        Args:
            audio: Audio samples
            sample_rate: Sample rate of audio

        Returns:
            Voice probability between 0 and 1
        """
        if not self._model_loaded:
            return 0.0

        try:
            import torch

            audio_tensor = torch.from_numpy(audio).float()
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)

            with torch.no_grad():
                speech_prob = self.model(audio_tensor, sample_rate).item()

            return speech_prob
        except Exception:
            return 0.0
