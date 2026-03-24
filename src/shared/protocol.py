"""Shared WebSocket protocol definitions for all services."""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""

    # Audio Bridge
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_OUTPUT = "audio_output"

    # STT
    TRANSCRIPTION = "transcription"
    START = "start"
    STOP = "stop"

    # LLM
    GENERATE = "generate"
    TOKEN = "token"
    DONE = "done"

    # TTS
    SYNTHESIZE = "synthesize"
    AUDIO = "audio"

    # Orchestrator
    LISTEN_START = "listen_start"
    LISTEN_STOP = "listen_stop"
    INTERRUPT = "interrupt"
    CONFIG = "config"
    STATUS = "status"
    ERROR = "error"


@dataclass
class AudioChunk:
    """Audio data chunk from input."""

    timestamp: int
    pcm_data: bytes
    chunk_duration_ms: int = 500
    sample_rate: int = 16000
    channels: int = 1

    def to_message(self) -> str:
        import base64

        return json.dumps(
            {
                "type": MessageType.AUDIO_CHUNK,
                "payload": {
                    "timestamp": self.timestamp,
                    "pcm_data": base64.b64encode(self.pcm_data).decode(),
                    "chunk_duration_ms": self.chunk_duration_ms,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels,
                },
            }
        )


@dataclass
class Transcription:
    """Transcription result from STT."""

    text: str
    is_final: bool
    confidence: float = 1.0
    timestamp_start: int = 0
    timestamp_end: int = 0

    def to_message(self) -> str:
        return json.dumps({"type": MessageType.TRANSCRIPTION, "payload": asdict(self)})

    @staticmethod
    def from_message(data: Dict[str, Any]) -> "Transcription":
        payload = data.get("payload", {})
        return Transcription(
            text=payload.get("text", ""),
            is_final=payload.get("is_final", False),
            confidence=payload.get("confidence", 1.0),
            timestamp_start=payload.get("timestamp_start", 0),
            timestamp_end=payload.get("timestamp_end", 0),
        )


@dataclass
class LLMToken:
    """Token from LLM streaming."""

    token: str
    is_final: bool = False

    def to_message(self) -> str:
        return json.dumps({"type": MessageType.TOKEN, "payload": asdict(self)})

    @staticmethod
    def from_message(data: Dict[str, Any]) -> "LLMToken":
        payload = data.get("payload", {})
        return LLMToken(
            token=payload.get("token", ""), is_final=payload.get("is_final", False)
        )


@dataclass
class TTSAudio:
    """Audio chunk from TTS."""

    audio_data: bytes
    is_final: bool
    duration_ms: int = 0

    def to_message(self) -> str:
        import base64

        return json.dumps(
            {
                "type": MessageType.AUDIO,
                "payload": {
                    "audio_data": base64.b64encode(self.audio_data).decode(),
                    "is_final": self.is_final,
                    "duration_ms": self.duration_ms,
                },
            }
        )

    @staticmethod
    def from_message(data: Dict[str, Any]) -> "TTSAudio":
        import base64

        payload = data.get("payload", {})
        audio_data = payload.get("audio_data", "")
        return TTSAudio(
            audio_data=base64.b64decode(audio_data) if audio_data else b"",
            is_final=payload.get("is_final", False),
            duration_ms=payload.get("duration_ms", 0),
        )


@dataclass
class ErrorMessage:
    """Error message from any service."""

    message: str
    code: Optional[str] = None

    def to_message(self) -> str:
        return json.dumps(
            {
                "type": MessageType.ERROR,
                "payload": {"message": self.message, "code": self.code},
            }
        )


@dataclass
class StatusMessage:
    """Pipeline status message."""

    state: str
    latency_ms: int = 0

    def to_message(self) -> str:
        return json.dumps({"type": MessageType.STATUS, "payload": asdict(self)})


def parse_message(raw: str) -> Dict[str, Any]:
    """Parse incoming WebSocket message."""
    return json.loads(raw)


def create_message(msg_type: MessageType, payload: Dict[str, Any]) -> str:
    """Create a WebSocket message."""
    return json.dumps({"type": msg_type, "payload": payload})
