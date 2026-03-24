"""STT Service - Parakeet-TDT 0.6B via sherpa-onnx with Offline Transducer.

Using OfflineRecognizer for chunk-based transcription with frame-by-frame simulation.

Architecture Benefits of Parakeet-TDT:
- Accurate speech recognition with low latency
- No hallucinations (Transducer architecture predicts "blanks" for silence)
- Real-Time Factor >100x on CPU
- 25 European languages support
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

# Try importing sherpa_onnx for real models
try:
    import sherpa_onnx

    SHERPA_AVAILABLE = True
except ImportError:
    SHERPA_AVAILABLE = False


class STTService:
    """Speech-to-Text using Parakeet-TDT 0.6B framework with OfflineRecognizer."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8001):
        self.host = host
        self.port = port
        self.recognizer: Optional[sherpa_onnx.OfflineRecognizer] = None
        self.clients: set = set()
        self._utterance_count = 0
        self.use_real_model = False

    async def load_model(self) -> None:
        """Load Parakeet-TDT 0.6B model with OfflineRecognizer."""
        logger.info("=" * 70)
        logger.info("STT SERVICE: Parakeet-TDT 0.6B with OfflineRecognizer")
        logger.info("=" * 70)

        # Try official sherpa-onnx model first
        official_model_path = os.environ.get(
            "PARAKEET_MODEL_PATH", "/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
        )

        encoder = f"{official_model_path}/encoder.int8.onnx"
        decoder = f"{official_model_path}/decoder.int8.onnx"
        joiner = f"{official_model_path}/joiner.int8.onnx"
        tokens = f"{official_model_path}/tokens.txt"

        logger.info(f"Checking for Parakeet-TDT model in {official_model_path}")

        # Try to load official sherpa-onnx model
        model_files_exist = all(
            os.path.exists(f) for f in [encoder, decoder, joiner, tokens]
        )

        if SHERPA_AVAILABLE and model_files_exist:
            try:
                logger.info("Official Parakeet-TDT v3 model files found - loading...")
                self.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                    encoder=encoder,
                    decoder=decoder,
                    joiner=joiner,
                    tokens=tokens,
                    num_threads=4,
                    model_type="nemo_transducer",
                )
                self.use_real_model = True
                logger.info(
                    "✅ Official Parakeet-TDT 0.6B v3 model loaded successfully!"
                )
                logger.info("   25 European languages supported")
                logger.info("   RTF: 0.118-0.325 on CPU (varies by language)")
                logger.info("=" * 70)

            except Exception as e:
                logger.warning(f"Could not load official model: {e}")
                logger.info("Falling back to intelligent dummy mode...")
                self._init_dummy_mode()
        else:
            if not SHERPA_AVAILABLE:
                logger.warning("sherpa_onnx library not available!")
            else:
                logger.info(f"Official model files not found in {official_model_path}")
            logger.info(
                "Using intelligent dummy implementation for pipeline testing..."
            )
            logger.info("\n📋 To use real Parakeet-TDT transcription:")
            logger.info("   Download: https://github.com/k2-fsa/sherpa-onnx/releases")
            logger.info(
                "   Look for: sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
            )
            logger.info("=" * 70)
            self._init_dummy_mode()

    def _init_dummy_mode(self) -> None:
        """Initialize dummy mode with intelligent test phrases."""
        logger.info("\n🎭 Using Intelligent Dummy STT")
        logger.info("   Returns rotating French phrases for pipeline testing")

    async def transcribe_audio(
        self, audio_data: bytes, sample_rate: int = 16000
    ) -> Transcription:
        """Transcribe audio using real or dummy implementation."""
        if self.use_real_model and self.recognizer:
            return await self._transcribe_real(audio_data, sample_rate)
        else:
            return await self._transcribe_dummy(audio_data, sample_rate)

    async def _transcribe_real(
        self, audio_data: bytes, sample_rate: int
    ) -> Transcription:
        """Transcribe using OfflineRecognizer with Parakeet-TDT v3."""
        try:
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            chunk_samples = len(audio_float32)
            chunk_ms = chunk_samples / sample_rate * 1000
            logger.info(
                f"Transcribing: {chunk_samples} samples ({chunk_ms:.0f}ms) at {sample_rate} Hz"
            )

            # Use OfflineRecognizer for batch transcription
            stream = self.recognizer.create_stream()
            stream.accept_waveform(sample_rate, audio_float32)
            self.recognizer.decode_stream(stream)
            result = stream.result
            text = result.text.strip()

            if text:
                logger.info(f"✓ Parakeet-TDT: '{text}'")
                confidence = 0.95
            else:
                logger.debug("No speech detected (silent chunk)")
                confidence = 0.0

            return Transcription(
                text=text,
                is_final=True,
                confidence=confidence,
                timestamp_start=0,
                timestamp_end=chunk_ms,
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return Transcription(text="", is_final=True, confidence=0.0)

    async def _transcribe_dummy(
        self, audio_data: bytes, sample_rate: int
    ) -> Transcription:
        """Transcribe using intelligent dummy (for testing)."""
        dummy_phrases = [
            "Bonjour, comment allez-vous aujourd'hui?",
            "Quel est votre nom?",
            "Pouvez-vous m'aider avec cette question?",
            "C'est une belle journée!",
            "Merci beaucoup pour votre aide.",
            "Que puis-je faire pour vous?",
            "À quelle heure est-il?",
            "Où est la gare la plus proche?",
        ]

        text = dummy_phrases[self._utterance_count % len(dummy_phrases)]
        self._utterance_count += 1

        logger.info(f"Dummy STT (phrase #{self._utterance_count}): '{text}'")

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

            transcription = await self.transcribe_audio(
                audio_bytes, sample_rate=sample_rate
            )

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
            if self.use_real_model:
                logger.info("✅ STT service listening - REAL Parakeet-TDT 0.6B!")
            else:
                logger.info(
                    "✅ STT service listening - Dummy mode (ready for real model)"
                )
            await asyncio.Future()


async def main():
    service = STTService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
