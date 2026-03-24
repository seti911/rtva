"""STT WebSocket client for connecting to STT service."""

import asyncio
import base64
import json
import logging
from typing import Optional, Callable, Awaitable
import websockets
from websockets.client import WebSocketClientProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


STTMessageHandler = Callable[[str, bool, float, int, int], Awaitable[None]]


class STTClient:
    """WebSocket client for STT service."""

    def __init__(self, url: str = "ws://localhost:8001/stt"):
        self.url = url
        self.ws: Optional[WebSocketClientProtocol] = None
        self.handler: Optional[STTMessageHandler] = None
        self._running = False

    def set_handler(self, handler: STTMessageHandler) -> None:
        """Set callback for transcription results."""
        self.handler = handler

    async def connect(self) -> bool:
        """Connect to STT service."""
        try:
            self.ws = await websockets.connect(self.url)
            logger.info(f"Connected to STT service at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to STT service: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from STT service."""
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def start(self, language: str = "fr", model: str = "small") -> None:
        """Start transcription stream."""
        if not self.ws:
            await self.connect()

        message = json.dumps(
            {
                "type": "start",
                "payload": {
                    "model": model,
                    "language": language,
                    "compute_type": "int8_float16",
                },
            }
        )
        await self.ws.send(message)
        self._running = True

    async def stop(self) -> None:
        """Stop transcription stream."""
        if self.ws:
            message = json.dumps({"type": "stop"})
            await self.ws.send(message)
            self._running = False

    async def send_audio(self, audio_data: bytes, timestamp: int = 0) -> None:
        """Send audio data to STT service."""
        if not self.ws:
            return

        message = json.dumps(
            {
                "type": "audio",
                "payload": {
                    "data": base64.b64encode(audio_data).decode(),
                    "timestamp": timestamp,
                },
            }
        )
        await self.ws.send(message)

    async def listen(self) -> None:
        """Listen for transcription results."""
        if not self.ws:
            return

        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("STT connection closed")

    async def _handle_message(self, message: str) -> None:
        """Handle incoming transcription message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "transcription" and self.handler:
                payload = data.get("payload", {})
                text = payload.get("text", "")
                is_final = payload.get("is_final", False)
                confidence = payload.get("confidence", 1.0)
                timestamp_start = payload.get("timestamp_start", 0)
                timestamp_end = payload.get("timestamp_end", 0)

                await self.handler(
                    text, is_final, confidence, timestamp_start, timestamp_end
                )

            elif msg_type == "error":
                payload = data.get("payload", {})
                logger.error(f"STT error: {payload.get('message')}")

        except json.JSONDecodeError:
            logger.error(f"Invalid message: {message}")


async def example_handler(
    text: str,
    is_final: bool,
    confidence: float,
    timestamp_start: int,
    timestamp_end: int,
) -> None:
    """Example handler for transcription results."""
    print(
        f"[{'FINAL' if is_final else 'PARTIAL'}] {text} (confidence: {confidence:.2f})"
    )


async def main():
    client = STTClient()
    client.set_handler(example_handler)

    if await client.connect():
        await client.start()
        await client.listen()


if __name__ == "__main__":
    asyncio.run(main())
