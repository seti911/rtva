"""STT Service - Streaming French Speech-to-Text using Parakeet-TDT 0.6B (Placeholder Implementation).

NOTE: This is a DUMMY implementation that returns placeholder French text.

For production use with real Parakeet-TDT 0.6B via sherpa-onnx:
1. Download the official model: https://github.com/k2-fsa/sherpa-onnx/releases
2. Use: sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8-fr.tar.bz2
3. Use the OnlineRecognizer API for true streaming with <50ms latency
4. The Transducer (TDT) architecture processes frame-by-frame with no hallucinations

This dummy version allows testing the full e2e pipeline: STT → LLM → TTS → Audio
"""

import asyncio
import base64
import json
import logging
import os
from typing import Optional, Dict, Any
import numpy as np
import websockets
from websockets.server import serve

from shared.protocol import Transcription, parse_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class STTService:
    """Dummy STT service returning placeholder French text for pipeline testing."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.clients: set = set()
        self._running = False
        self._utterance_count = 0

    async def load_model(self) -> None:
        """Initialize dummy model (no actual model loading)."""
        logger.warning("=" * 70)
        logger.warning("DUMMY STT SERVICE - Using placeholder French text")
        logger.warning("For production, deploy real Parakeet-TDT 0.6B via sherpa-onnx:")
        logger.warning(
            "  - Download: sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8-fr.tar.bz2"
        )
        logger.warning("  - Use OnlineRecognizer for streaming (<50ms latency)")
        logger.warning(
            "  - Frame-by-frame processing eliminates Whisper hallucinations"
        )
        logger.warning("=" * 70)

    async def transcribe(
        self, audio_data: bytes, language: str = "fr", sample_rate: int = 16000
    ) -> Transcription:
        """Return dummy transcription for testing pipeline."""
        # Placeholder French sentences for testing
        dummy_transcriptions = [
            "Bonjour, comment allez-vous aujourd'hui?",
            "Quel est votre nom?",
            "Pouvez-vous m'aider avec cette question?",
            "C'est une belle journée!",
            "Merci beaucoup pour votre aide.",
        ]

        text = dummy_transcriptions[self._utterance_count % len(dummy_transcriptions)]
        self._utterance_count += 1

        logger.info(f"Dummy STT (utterance #{self._utterance_count}): '{text}'")

        return Transcription(
            text=text,
            is_final=True,
            confidence=0.95,
            timestamp_start=0,
            timestamp_end=len(audio_data) / sample_rate * 1000,
        )

    async def handle_client(self, client) -> None:
        """Handle WebSocket client connection."""
        client_id = id(client)
        self.clients.add(client)
        logger.info(f"Client {client_id} connected")

        try:
            async for message in client:
                await self.process_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.clients.discard(client)

    async def process_message(self, client, message: str) -> None:
        """Process incoming message."""
        try:
            data = parse_message(message)
            msg_type = data.get("type")

            if msg_type == "audio":
                await self.handle_audio(client, data)
            elif msg_type == "start":
                await self.handle_start(client, data)
            elif msg_type == "stop":
                await self.handle_stop(client, data)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await client.send(
                json.dumps({"type": "error", "payload": {"message": str(e)}})
            )

    async def handle_audio(self, client, data: Dict[str, Any]) -> None:
        """Handle incoming audio data."""
        payload = data.get("payload", {})
        pcm_data = payload.get("pcm_data", "")
        sample_rate = payload.get("sample_rate", 16000)

        if pcm_data:
            audio_bytes = base64.b64decode(pcm_data)
            logger.info(f"Audio chunk: {len(audio_bytes)} bytes at {sample_rate} Hz")

            transcription = await self.transcribe(audio_bytes, sample_rate=sample_rate)
            logger.info(f"Transcription: '{transcription.text}'")

            if transcription.text:
                response = transcription.to_message()
                await client.send(response)

    async def handle_start(self, client, data: Dict[str, Any]) -> None:
        """Handle start transcription request."""
        logger.info("Starting transcription session")

    async def handle_stop(self, client, data: Dict[str, Any]) -> None:
        """Handle stop transcription request."""
        logger.info("Stopping transcription session")

    async def start(self) -> None:
        """Start the STT service."""
        await self.load_model()

        logger.info(f"Starting STT service on ws://{self.host}:{self.port}")

        async with serve(self.handle_client, self.host, self.port):
            logger.info("STT service listening")
            await asyncio.Future()


async def main():
    service = STTService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
