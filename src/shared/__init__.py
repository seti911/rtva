"""Shared utilities for voice assistant services."""

from .protocol import (
    MessageType,
    AudioChunk,
    Transcription,
    LLMToken,
    TTSAudio,
    ErrorMessage,
    StatusMessage,
    parse_message,
    create_message,
)
from .audio import (
    AudioFormat,
    AudioBuffer,
    encode_pcm16,
    decode_pcm16,
    resample,
    normalize,
    detect_silence,
    calculate_rms,
)
from .base_service import BaseService

__all__ = [
    "MessageType",
    "AudioChunk",
    "Transcription",
    "LLMToken",
    "TTSAudio",
    "ErrorMessage",
    "StatusMessage",
    "parse_message",
    "create_message",
    "AudioFormat",
    "AudioBuffer",
    "encode_pcm16",
    "decode_pcm16",
    "resample",
    "normalize",
    "detect_silence",
    "calculate_rms",
    "BaseService",
]
