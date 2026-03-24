"""STT Service - Speech to Text using Parakeet TDT via sherpa-onnx (25 European Languages)."""

import asyncio
import base64
import json
import logging
import os
from typing import Optional, Dict, Any
import numpy as np
import websockets
from websockets.server import WebSocketServerProtocol

import sherpa_onnx
from sherpa_onnx import OfflineRecognizer

from shared.protocol import Transcription, parse_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Parakeet via sherpa-onnx."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.model: Optional[OfflineRecognizer] = None
        self.clients: set = set()
        self._running = False
        self._audio_buffer = {}

    async def load_model(self) -> None:
        """Load the Parakeet model via sherpa-onnx."""
        model_path = os.environ.get("PARAKEET_MODEL_PATH", "/models/parakeet")

        encoder = f"{model_path}/encoder.int8.onnx"
        decoder = f"{model_path}/decoder.int8.onnx"
        joiner = f"{model_path}/joiner.int8.onnx"
        tokens = f"{model_path}/tokens.txt"

        logger.info(f"Loading Parakeet model from {model_path}")
        logger.info(f"Encoder: {encoder}")
        logger.info(f"Decoder: {decoder}")
        logger.info(f"Joinser: {joiner}")
        logger.info(f"Tokens: {tokens}")

        self.model = OfflineRecognizer.from_transducer(
            encoder=encoder,
            decoder=decoder,
            joiner=joiner,
            tokens=tokens,
        )
        logger.info("Parakeet model loaded successfully")

    async def transcribe(
        self, audio_data: bytes, language: str = "fr"
    ) -> Transcription:
        """Transcribe audio data."""
        if not self.model:
            return Transcription(text="", is_final=True, confidence=0.0)

        try:
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            logger.info(f"Transcribing {len(audio_float32)} samples")

            stream = self.model.create_stream()
            stream.accept_waveform(16000, audio_float32)
            self.model.decode_stream(stream)
            text = stream.result.text

            logger.info(f"Parakeet transcription: '{text}'")

            return Transcription(
                text=text.strip(),
                is_final=True,
                confidence=0.9,
                timestamp_start=0,
                timestamp_end=len(audio_data) / 16000 * 1000,
            )

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return Transcription(text="", is_final=True, confidence=0.0)

    async def handle_client(self, client: WebSocketServerProtocol) -> None:
        """Handle WebSocket client connection."""
        self.clients.add(client)
        client_id = id(client)
        logger.info(f"Client {client_id} connected")
        self._audio_buffer[client_id] = b""

        try:
            async for message in client:
                await self.process_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.clients.discard(client)
            self._audio_buffer.pop(client_id, None)

    async def process_message(
        self, client: WebSocketServerProtocol, message: str
    ) -> None:
        """Process incoming message."""
        data = parse_message(message)
        msg_type = data.get("type")

        if msg_type == "audio":
            await self.handle_audio(client, data)
        elif msg_type == "start":
            await self.handle_start(client, data)
        elif msg_type == "stop":
            await self.handle_stop(client, data)

    async def handle_audio(
        self, client: WebSocketServerProtocol, data: Dict[str, Any]
    ) -> None:
        """Handle incoming audio data."""
        payload = data.get("payload", {})
        pcm_data = payload.get("pcm_data", "")

        if pcm_data:
            audio_bytes = base64.b64decode(pcm_data)
            self._audio_buffer[id(client)] += audio_bytes

            logger.info(f"Audio chunk: {len(audio_bytes)} bytes")
            transcription = await self.transcribe(audio_bytes)
            logger.info(f"Transcription result: '{transcription.text}'")

            if transcription.text:
                response = transcription.to_message()
                await client.send(response)

    async def handle_start(
        self, client: WebSocketServerProtocol, data: Dict[str, Any]
    ) -> None:
        """Handle start transcription request."""
        logger.info("Starting transcription")

    async def handle_stop(
        self, client: WebSocketServerProtocol, data: Dict[str, Any]
    ) -> None:
        """Handle stop transcription request."""
        client_id = id(client)
        if client_id in self._audio_buffer and self._audio_buffer[client_id]:
            audio_bytes = self._audio_buffer[client_id]
            transcription = await self.transcribe(audio_bytes)
            transcription.is_final = True
            response = transcription.to_message()
            await client.send(response)
            self._audio_buffer[client_id] = b""

    async def start(self) -> None:
        """Start the STT service."""
        if not self.model:
            await self.load_model()

        logger.info(f"Starting STT service on ws://{self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("STT service listening")
            await asyncio.Future()


async def main():
    service = STTService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
