"""LLM WebSocket client for connecting to LLM service."""

import asyncio
import json
import logging
from typing import Optional, Callable, Awaitable, List
import websockets
from websockets.client import WebSocketClientProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TokenHandler = Callable[[str, bool], Awaitable[None]]
DoneHandler = Callable[[str, int], Awaitable[None]]


class LLMClient:
    """WebSocket client for LLM service."""

    def __init__(self, url: str = "ws://localhost:8002/llm"):
        self.url = url
        self.ws: Optional[WebSocketClientProtocol] = None
        self.token_handler: Optional[TokenHandler] = None
        self.done_handler: Optional[DoneHandler] = None
        self._running = False

    def set_token_handler(self, handler: TokenHandler) -> None:
        """Set callback for streaming tokens."""
        self.token_handler = handler

    def set_done_handler(self, handler: DoneHandler) -> None:
        """Set callback for generation complete."""
        self.done_handler = handler

    async def connect(self) -> bool:
        """Connect to LLM service."""
        try:
            self.ws = await websockets.connect(self.url)
            logger.info(f"Connected to LLM service at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to LLM service: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from LLM service."""
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = True,
    ) -> None:
        """Send generation request."""
        if not self.ws:
            await self.connect()

        message = json.dumps(
            {
                "type": "generate",
                "payload": {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream,
                },
            }
        )
        await self.ws.send(message)
        self._running = True

    async def stop(self) -> None:
        """Stop generation."""
        if self.ws:
            message = json.dumps({"type": "stop"})
            await self.ws.send(message)
            self._running = False

    async def listen(self) -> None:
        """Listen for generation results."""
        if not self.ws:
            return

        full_text = ""
        tokens_count = 0

        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "token":
                    payload = data.get("payload", {})
                    token = payload.get("token", "")
                    is_final = payload.get("is_final", False)

                    full_text += token
                    tokens_count += 1

                    if self.token_handler:
                        await self.token_handler(token, is_final)

                elif msg_type == "done":
                    payload = data.get("payload", {})
                    full_text = payload.get("full_text", full_text)
                    tokens_count = payload.get("tokens_generated", tokens_count)

                    if self.done_handler:
                        await self.done_handler(full_text, tokens_count)

                    self._running = False
                    break

                elif msg_type == "error":
                    payload = data.get("payload", {})
                    logger.error(f"LLM error: {payload.get('message')}")
                    self._running = False
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info("LLM connection closed")


async def token_handler(token: str, is_final: bool) -> None:
    """Example token handler."""
    print(f"Token: {token}", end="", flush=True)


async def done_handler(full_text: str, tokens_count: int) -> None:
    """Example done handler."""
    print(f"\n\nGeneration complete: {tokens_count} tokens")


async def main():
    client = LLMClient()
    client.set_token_handler(token_handler)
    client.set_done_handler(done_handler)

    if await client.connect():
        prompt = "[INST] Bonjour, comment allez-vous ?\n Assistant:"
        await client.generate(prompt)
        await client.listen()


if __name__ == "__main__":
    asyncio.run(main())
