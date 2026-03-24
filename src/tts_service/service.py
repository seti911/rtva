"""TTS Service - Text to Speech using gTTS (fallback for XTTS)."""

import asyncio
import base64
import logging
import json
import os
from typing import Optional
import numpy as np
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using gTTS (fallback)."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8003):
        self.host = host
        self.port = port
        self.tts = None
        self.clients: set = set()
        self.use_gtts = True

    async def load_model(self) -> None:
        """Load the TTS model."""
        try:
            from TTS.api import TTS

            logger.info("Loading XTTS model...")
            self.tts = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True
            )
            self.use_gtts = False
            logger.info("XTTS model loaded successfully")
        except Exception as e:
            logger.error(f"XTTS load error: {e}")
            self.use_gtts = True

    async def synthesize(
        self, text: str, language: str = "fr", reference_wav: Optional[bytes] = None
    ) -> tuple[bytes, int]:
        """Synthesize speech from text."""
        try:
            if self.use_gtts:
                return await self._synthesize_gtts(text, language)
            else:
                return await self._synthesize_xtts(text, language, reference_wav)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return b"", 0

    async def _synthesize_gtts(
        self, text: str, language: str = "fr"
    ) -> tuple[bytes, int]:
        """Synthesize using gTTS."""
        try:
            from gtts import gTTS
            import io

            lang_map = {"fr": "fr", "en": "en", "es": "es", "de": "de"}
            lang = lang_map.get(language, "fr")

            tts = gTTS(text=text, lang=lang, slow=False)

            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)

            import subprocess

            wav_buffer = io.BytesIO()
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    "pipe:0",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                    "-f",
                    "s16le",
                    "-",
                ],
                input=mp3_buffer.read(),
                capture_output=True,
            )

            if result.returncode == 0 and len(result.stdout) > 0:
                audio_bytes = result.stdout
            else:
                # Return placeholder beep if ffmpeg fails
                logger.warning("gTTS ffmpeg failed, returning placeholder")
                audio_bytes = self._generate_beep()

            duration_ms = int(len(audio_bytes) / 24000 * 1000)
            return audio_bytes, duration_ms

        except Exception as e:
            logger.error(f"gTTS error: {e}")
            # Return placeholder audio
            return self._generate_beep(), 500

    def _trim_silence(
        self,
        audio_bytes: bytes,
        threshold: int = 1000,
        min_silence_duration: int = 4800,
    ) -> bytes:
        """Trim trailing silence from audio.

        Args:
            audio_bytes: Raw PCM audio data (16-bit, little-endian)
            threshold: Amplitude threshold for silence detection
            min_silence_duration: Minimum samples of silence to trim

        Returns:
            Audio bytes with trailing silence removed
        """
        if not audio_bytes:
            return audio_bytes

        audio = np.frombuffer(audio_bytes, dtype=np.int16)

        # Find last non-silent sample
        for i in range(len(audio) - 1, -1, -1):
            if abs(audio[i]) > threshold:
                # Check if we have enough silence after this point
                silence_after = len(audio) - i - 1
                if silence_after >= min_silence_duration:
                    # Trim the silence
                    audio = audio[: i + 1]
                    break

        return audio.astype(np.int16).tobytes()

    def _generate_beep(self) -> bytes:
        """Generate a simple beep as placeholder."""
        import numpy as np

        frequency = 440  # Hz
        duration = 0.5  # seconds
        sample_rate = 24000

        t = np.linspace(0, duration, int(sample_rate * duration))
        beep = np.sin(2 * np.pi * frequency * t) * 0.3
        beep = (beep * 32767).astype(np.int16)
        return beep.tobytes()

    async def _synthesize_xtts(
        self, text: str, language: str = "fr", reference_wav: Optional[bytes] = None
    ) -> tuple[bytes, int]:
        """Synthesize using XTTS."""
        import tempfile
        import os

        ref_path = None
        if reference_wav:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as ref_file:
                ref_file.write(reference_wav)
                ref_path = ref_file.name

        # Use first available speaker if no reference provided
        speaker = None if ref_path else "Daisy Studious"
        wav = self.tts.tts(
            text=text, language=language, speaker_wav=ref_path, speaker=speaker
        )

        if ref_path and os.path.exists(ref_path):
            os.unlink(ref_path)

        # Handle list return type
        if isinstance(wav, list):
            wav = np.array(wav)

        audio_int16 = (wav * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        duration_ms = int(len(wav) / 24000 * 1000)

        return audio_bytes, duration_ms

    async def handle_client(self, client: WebSocketServerProtocol) -> None:
        """Handle WebSocket client connection."""
        self.clients.add(client)
        client_id = id(client)
        logger.info(f"TTS Client {client_id} connected")

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

            if msg_type == "synthesize":
                await self.handle_synthesize(client, data)
            elif msg_type == "stop":
                logger.info("Stop synthesis requested")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            await client.send(
                json.dumps({"type": "error", "payload": {"message": str(e)}})
            )

    async def handle_synthesize(
        self, client: WebSocketServerProtocol, data: dict
    ) -> None:
        """Handle synthesis request."""
        payload = data.get("payload", {})
        text = payload.get("text", "")
        language = payload.get("language", "fr")
        reference_wav_b64 = payload.get("reference_wav", "")

        reference_wav = None
        if reference_wav_b64:
            reference_wav = base64.b64decode(reference_wav_b64)

        logger.info(f"Synthesizing: {text[:50]}...")

        audio_bytes, duration_ms = await self.synthesize(text, language, reference_wav)

        # Trim trailing silence to avoid artifacts at chunk boundaries
        if audio_bytes:
            audio_bytes = self._trim_silence(audio_bytes)
            # Recalculate duration after trimming
            duration_ms = int(len(audio_bytes) / 24000 * 1000)

        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode()

            response = json.dumps(
                {
                    "type": "audio",
                    "payload": {
                        "audio_data": audio_b64,
                        "is_final": True,
                        "duration_ms": duration_ms,
                    },
                }
            )
            await client.send(response)
        else:
            await client.send(
                json.dumps(
                    {"type": "error", "payload": {"message": "Synthesis failed"}}
                )
            )

    async def start(self) -> None:
        """Start the TTS service."""
        await self.load_model()

        logger.info(f"Starting TTS service on ws://{self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("TTS service listening")
            await asyncio.Future()


async def main():
    service = TTSService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
