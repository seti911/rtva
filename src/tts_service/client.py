"""TTS WebSocket client for connecting to TTS service."""

import asyncio
import base64
import json
import logging
from typing import Optional, Callable, Awaitable
import websockets
from websockets.client import WebSocketClientProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AudioHandler = Callable[[bytes, bool, int], Awaitable[None]]


class TTSClient:
    """WebSocket client for TTS service."""

    def __init__(self, url: str = "ws://localhost:8003/tts"):
        self.url = url
        self.ws: Optional[WebSocketClientProtocol] = None
        self.audio_handler: Optional[AudioHandler] = None
        self._running = False

    def set_audio_handler(self, handler: AudioHandler) -> None:
        """Set callback for audio chunks."""
        self.audio_handler = handler

    async def connect(self) -> bool:
        """Connect to TTS service."""
        try:
            self.ws = await websockets.connect(self.url)
            logger.info(f"Connected to TTS service at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TTS service: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from TTS service."""
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def synthesize(
        self, text: str, language: str = "fr", reference_wav: Optional[bytes] = None
    ) -> None:
        """Send synthesis request."""
        if not self.ws:
            await self.connect()

        payload = {"text": text, "language": language, "stream": True}

        if reference_wav:
            payload["reference_wav"] = base64.b64encode(reference_wav).decode()

        message = json.dumps({"type": "synthesize", "payload": payload})

        await self.ws.send(message)
        self._running = True

    async def stop(self) -> None:
        """Stop synthesis."""
        if self.ws:
            message = json.dumps({"type": "stop"})
            await self.ws.send(message)
            self._running = False

    async def listen(self) -> None:
        """Listen for audio chunks."""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("TTS connection closed")

    async def _handle_message(self, message: str) -> None:
        """Handle incoming audio message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "audio" and self.audio_handler:
                payload = data.get("payload", {})
                audio_data_b64 = payload.get("audio_data", "")
                is_final = payload.get("is_final", False)
                duration_ms = payload.get("duration_ms", 0)

                audio_data = base64.b64decode(audio_data_b64) if audio_data_b64 else b""

                await self.audio_handler(audio_data, is_final, duration_ms)

                if is_final:
                    self._running = False

            elif msg_type == "error":
                payload = data.get("payload", {})
                logger.error(f"TTS error: {payload.get('message')}")
                self._running = False

        except json.JSONDecodeError:
            logger.error(f"Invalid message: {message}")


async def audio_handler(audio_data: bytes, is_final: bool, duration_ms: int) -> None:
    """Example audio handler - plays audio."""
    print(
        f"Audio chunk received: {len(audio_data)} bytes, duration: {duration_ms}ms, final: {is_final}"
    )

    if audio_data:
        import numpy as np
        import sounddevice as sd

        audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        sd.play(audio_float32, 24000)
        if is_final:
            sd.wait()


async def main():
    client = TTSClient()
    client.set_audio_handler(audio_handler)

    if await client.connect():
        await client.synthesize("Bonjour, je suis votre assistant vocal.")
        await client.listen()


if __name__ == "__main__":
    asyncio.run(main())
