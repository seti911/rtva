"""LLM Service - Local LLM using llama-cpp-python with CroissantLLM."""

import asyncio
import logging
import json
import os
from typing import Optional
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """LLM service using CroissantLLM via llama-cpp-python."""

    def __init__(
        self,
        model_path: str = "/models/croissant/CroissantLLMChat-v0.1-Q3_K_M.gguf",
        host: str = "0.0.0.0",
        port: int = 8002,
    ):
        self.model_path = os.environ.get("MODEL_PATH", model_path)
        self.host = host
        self.port = port
        self.clients: set = set()
        self.model = None
        self._running = False

    async def load_model(self) -> None:
        """Load the LLM model."""
        try:
            from llama_cpp import Llama

            logger.info(f"Loading LLM model from {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=0,  # CPU only by default
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.model = None

    async def generate_stream(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.3
    ) -> list[str]:
        """Generate tokens from prompt using CroissantLLM chat format."""
        if not self.model:
            return ["Désolé, le modèle n'est pas chargé."]

        try:
            # Format prompt for CroissantLLM chat
            chat_prompt = f"""<|im_start|>system
Tu es un assistant vocal poli et utile.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""

            tokens = []
            for token in self.model(
                chat_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                stop=["<|im_end|>", "<|im_start|>"],
            ):
                if "choices" in token and len(token["choices"]) > 0:
                    text = token["choices"][0].get("text", "")
                    if text:
                        tokens.append(text)
            return tokens
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return [f"Erreur: {str(e)}"]

    async def handle_client(self, client: WebSocketServerProtocol) -> None:
        """Handle WebSocket client connection."""
        self.clients.add(client)
        client_id = id(client)
        logger.info(f"LLM Client {client_id} connected")

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
        """Process incoming message."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "generate":
                await self.handle_generate(client, data)
            elif msg_type == "stop":
                logger.info("Stop generation requested")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            await client.send(
                json.dumps({"type": "error", "payload": {"message": str(e)}})
            )

    async def handle_generate(
        self, client: WebSocketServerProtocol, data: dict
    ) -> None:
        """Handle generation request."""
        payload = data.get("payload", {})
        prompt = payload.get("prompt", "")
        max_tokens = payload.get("max_tokens", 256)
        temperature = payload.get("temperature", 0.7)

        logger.info(f"Generating response for prompt: {prompt[:50]}...")

        # Generate tokens
        tokens = await self.generate_stream(prompt, max_tokens, temperature)

        # Stream tokens to client
        for i, token in enumerate(tokens):
            is_final = i == len(tokens) - 1
            token_msg = json.dumps(
                {"type": "token", "payload": {"token": token, "is_final": False}}
            )
            await client.send(token_msg)
            await asyncio.sleep(0.02)

        # Send done
        full_text = "".join(tokens)
        final_msg = json.dumps(
            {
                "type": "done",
                "payload": {"full_text": full_text, "tokens_generated": len(tokens)},
            }
        )
        await client.send(final_msg)

    async def start(self) -> None:
        """Start the LLM service."""
        # Try to load model but continue if it fails
        try:
            await self.load_model()
        except Exception as e:
            logger.warning(f"Model not loaded, using placeholder: {e}")

        logger.info(f"Starting LLM service on ws://{self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("LLM service listening")
            await asyncio.Future()


async def main():
    model_path = os.environ.get(
        "LLM_MODEL_PATH", "/models/mistral/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    )
    service = LLMService(model_path)
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
