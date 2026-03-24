"""Orchestrator - Coordinates all voice assistant services."""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any
import websockets
from websockets import connect
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates the voice assistant pipeline."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port

        # Service URLs
        self.stt_url = os.environ.get("STT_URL", "ws://localhost:8001/stt")
        self.llm_url = os.environ.get("LLM_URL", "ws://localhost:8002/llm")
        self.tts_url = os.environ.get("TTS_URL", "ws://localhost:8003/tts")

        # Service connections
        self.stt_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.llm_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.tts_ws: Optional[websockets.WebSocketClientProtocol] = None

        # Client connections
        self.clients: set = set()

        # State
        self.state = "idle"
        self.config = {
            "language": "fr",
            "voice_reference": None,
            "llm_temperature": 0.7,
            "stt_model": "small",
        }

        # Buffers
        self.token_buffer = ""
        self.last_token_time = 0

    async def connect_services(self) -> bool:
        """Connect to all backend services."""
        try:
            logger.info("Connecting to services...")

            # Try to connect to STT (optional - can work without it)
            try:
                self.stt_ws = await connect(self.stt_url)
                logger.info("Connected to STT service")
            except Exception as e:
                logger.warning(
                    f"Could not connect to STT service: {e}, continuing without STT"
                )

            self.llm_ws = await connect(self.llm_url)
            logger.info("Connected to LLM service")

            self.tts_ws = await connect(self.tts_url)
            logger.info("Connected to TTS service")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to services: {e}")
            return False

    async def disconnect_services(self) -> None:
        """Disconnect from all backend services."""
        if self.stt_ws:
            await self.stt_ws.close()
        if self.llm_ws:
            await self.llm_ws.close()
        if self.tts_ws:
            await self.tts_ws.close()

    async def handle_client(self, client: WebSocketServerProtocol) -> None:
        """Handle client WebSocket connection."""
        self.clients.add(client)
        client_id = id(client)
        logger.info(f"Client {client_id} connected")

        try:
            async for message in client:
                await self.process_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.clients.discard(client)

    async def process_message(
        self, client: WebSocketServerProtocol, message: str
    ) -> None:
        """Process incoming message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            logger.info(f"Received message type: {msg_type}")

            if msg_type == "listen_start":
                await self.handle_listen_start(client, data)
            elif msg_type == "listen_stop":
                await self.handle_listen_stop(client, data)
            elif msg_type == "interrupt":
                await self.handle_interrupt(client, data)
            elif msg_type == "config":
                await self.handle_config(client, data)
            elif msg_type == "transcription":
                await self.handle_transcription(client, data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")

    async def handle_listen_start(
        self, client: WebSocketServerProtocol, data: Dict
    ) -> None:
        """Handle start listening request."""
        self.state = "listening"
        await self.broadcast_status()

        if not self.stt_ws:
            connected = await self.connect_services()
            if not connected:
                await client.send(
                    json.dumps(
                        {
                            "type": "error",
                            "payload": {
                                "message": "Failed to connect to services",
                                "code": "CONNECTION_ERROR",
                            },
                        }
                    )
                )
                return

        start_msg = json.dumps(
            {"type": "start", "payload": {"language": self.config["language"]}}
        )
        if self.stt_ws:
            await self.stt_ws.send(start_msg)

    async def handle_listen_stop(
        self, client: WebSocketServerProtocol, data: Dict
    ) -> None:
        """Handle stop listening request."""
        self.state = "idle"
        await self.broadcast_status()

        if self.stt_ws:
            stop_msg = json.dumps({"type": "stop"})
            await self.stt_ws.send(stop_msg)

    async def handle_interrupt(
        self, client: WebSocketServerProtocol, data: Dict
    ) -> None:
        """Handle user interrupt (speaking over assistant)."""
        self.state = "interrupted"
        await self.broadcast_status()

        # Stop current processing
        if self.llm_ws:
            await self.llm_ws.send(json.dumps({"type": "stop"}))
        if self.tts_ws:
            await self.tts_ws.send(json.dumps({"type": "stop"}))

        # Clear buffers
        self.token_buffer = ""

        # Return to listening
        self.state = "listening"
        await self.broadcast_status()

    async def handle_config(self, client: WebSocketServerProtocol, data: Dict) -> None:
        """Handle configuration update."""
        payload = data.get("payload", {})
        self.config.update(payload)
        await client.send(
            json.dumps(
                {
                    "type": "status",
                    "payload": {"state": self.state, "config": self.config},
                }
            )
        )

    async def handle_transcription(
        self, client: WebSocketServerProtocol, data: Dict
    ) -> None:
        """Handle incoming transcription and start pipeline."""
        payload = data.get("payload", {})
        text = payload.get("text", "")
        is_final = payload.get("is_final", False)

        if not text:
            return

        # Connect to services if not connected
        if not self.llm_ws:
            logger.info("Connecting to services...")
            connected = await self.connect_services()
            if not connected:
                logger.error("Failed to connect to services")
                await self.broadcast(
                    {
                        "type": "error",
                        "payload": {
                            "message": "Failed to connect to services",
                            "code": "CONNECTION_ERROR",
                        },
                    }
                )
                return

        logger.info(f"Received transcription: {text}")

        # Broadcast transcription
        await self.broadcast(
            {"type": "transcription", "payload": {"text": text, "is_final": is_final}}
        )

        if is_final:
            await self.process_with_llm(text)

    async def process_with_llm(self, prompt: str) -> None:
        """Process text with LLM and generate response with streaming."""
        self.state = "processing"
        await self.broadcast_status()

        full_prompt = f"[INST]Tu es un assistant vocal. Réponds brièvement en français.\n\nUser: {prompt}\nAssistant:"

        llm_request = json.dumps(
            {
                "type": "generate",
                "payload": {
                    "prompt": full_prompt,
                    "max_tokens": 128,
                    "temperature": self.config["llm_temperature"],
                    "stream": True,
                },
            }
        )

        await self.llm_ws.send(llm_request)

        # Streaming state
        full_response = ""
        tts_buffer = ""
        self.state = "speaking"
        await self.broadcast_status()

        try:
            async for message in self.llm_ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "token":
                    token = data.get("payload", {}).get("token", "")
                    full_response += token
                    tts_buffer += token

                    # Stream token to client immediately
                    await self.broadcast(
                        {"type": "llm_token", "payload": {"token": token}}
                    )

                    logger.info(f"LLM token: {token}")

                    # Send to TTS when buffer has enough text or punctuation
                    if self.should_send_to_tts(tts_buffer):
                        asyncio.create_task(self.process_with_tts(tts_buffer))
                        tts_buffer = ""

                elif msg_type == "done":
                    logger.info(f"LLM done, full response: {full_response}")

                    # Send remaining buffer to TTS
                    if tts_buffer.strip():
                        await self.process_with_tts(tts_buffer)

                    await asyncio.sleep(1)
                    self.state = "listening"
                    await self.broadcast_status()
                    break

        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            self.state = "listening"
            await self.broadcast_status()

    def should_send_to_tts(self, buffer: str) -> bool:
        """Determine if buffer should be sent to TTS."""
        # Send on sentence-ending punctuation
        if buffer.strip()[-1:] in ".!?" and len(buffer.strip()) > 10:
            return True
        # Send when buffer is large enough (~3 seconds of speech)
        if len(buffer) > 100:
            return True
        return False

    def should_trigger_tts(self, token: str) -> bool:
        """Determine if we should send buffer to TTS."""
        # Trigger on punctuation
        if token.strip()[-1:] in ".!?":
            return True
        # Trigger on buffer size
        if len(self.token_buffer.split()) >= 20:
            return True
        return False

    async def process_with_tts(self, text: str) -> None:
        """Convert text to speech and stream to clients."""
        if not text.strip():
            return

        if not self.tts_ws:
            logger.error("TTS service not connected")
            return

        logger.info(f"Synthesizing: {text[:50]}...")

        tts_request = json.dumps(
            {
                "type": "synthesize",
                "payload": {
                    "text": text,
                    "language": self.config["language"],
                    "reference_wav": self.config.get("voice_reference"),
                },
            }
        )

        await self.tts_ws.send(tts_request)

        try:
            message = await self.tts_ws.recv()
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "audio":
                payload = data.get("payload", {})
                audio_data = payload.get("audio_data", "")
                duration_ms = payload.get("duration_ms", 0)

                logger.info(f"TTS audio received: {duration_ms}ms")

                await self.broadcast(
                    {
                        "type": "audio_output",
                        "payload": {"data": audio_data, "duration_ms": duration_ms},
                    }
                )

        except Exception as e:
            logger.error(f"TTS error: {e}")

    async def broadcast(self, message: Dict) -> None:
        """Broadcast message to all connected clients."""
        if self.clients:
            msg_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(msg_str) for client in self.clients],
                return_exceptions=True,
            )

    async def broadcast_status(self) -> None:
        """Broadcast current status to all clients."""
        await self.broadcast(
            {"type": "status", "payload": {"state": self.state, "latency_ms": 0}}
        )

    async def start(self) -> None:
        """Start the orchestrator."""
        logger.info(f"Starting orchestrator on ws://{self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("Orchestrator listening")
            await asyncio.Future()


async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
