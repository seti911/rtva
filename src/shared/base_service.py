"""Base service class for all voice assistant services."""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all WebSocket services."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.clients: set = set()
        self._running = False

    @abstractmethod
    async def handle_message(
        self, client: WebSocketServerProtocol, message: str
    ) -> None:
        """Handle incoming WebSocket message. Override in subclass."""
        pass

    @abstractmethod
    async def on_connect(self, client: WebSocketServerProtocol) -> None:
        """Called when a client connects. Override in subclass."""
        pass

    @abstractmethod
    async def on_disconnect(self, client: WebSocketServerProtocol) -> None:
        """Called when a client disconnects. Override in subclass."""
        pass

    async def client_handler(self, client: WebSocketServerProtocol, path: str) -> None:
        """Handle a single client connection."""
        self.clients.add(client)
        client_id = id(client)
        logger.info(f"Client {client_id} connected from {client.remote_address}")

        try:
            await self.on_connect(client)

            async for message in client:
                await self.handle_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(client)
            await self.on_disconnect(client)

    async def broadcast(self, message: str) -> None:
        """Broadcast message to all connected clients."""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True,
            )

    async def send_to(self, client: WebSocketServerProtocol, message: str) -> None:
        """Send message to specific client."""
        try:
            await client.send(message)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def start(self) -> None:
        """Start the WebSocket server."""
        logger.info(f"Starting {self.__class__.__name__} on {self.host}:{self.port}")

        self._running = True

        async with websockets.serve(self.client_handler, self.host, self.port):
            logger.info(
                f"{self.__class__.__name__} listening on ws://{self.host}:{self.port}"
            )
            await asyncio.Future()

    def stop(self) -> None:
        """Stop the WebSocket server."""
        logger.info(f"Stopping {self.__class__.__name__}")
        self._running = False

    def parse_message(self, raw: str) -> Dict[str, Any]:
        """Parse incoming JSON message."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            return {"type": "error", "payload": {"message": str(e)}}

    def create_error(self, message: str, code: Optional[str] = None) -> str:
        """Create error message."""
        return json.dumps(
            {"type": "error", "payload": {"message": message, "code": code}}
        )
