"""Phrase chunking logic for natural TTS output."""

import re
import time
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ChunkerConfig:
    """Configuration for phrase chunking."""

    max_tokens: int = 20
    min_phrase_length: int = 3
    punctuation_markers: List[str] = field(default_factory=lambda: [".", "!", "?"])
    pause_threshold_ms: int = 200


class PhraseChunker:
    """Chunks LLM token stream into phrases for TTS."""

    def __init__(self, config: Optional[ChunkerConfig] = None):
        self.config = config or ChunkerConfig()
        self.buffer = ""
        self.last_token_time = time.time()
        self.token_count = 0

    def add_token(self, token: str) -> Optional[str]:
        """
        Add a token to the buffer.

        Args:
            token: New token from LLM

        Returns:
            Complete phrase if chunking triggered, None otherwise
        """
        self.buffer += token
        self.token_count += 1
        current_time = time.time()
        time_since_last_token_ms = (current_time - self.last_token_time) * 1000
        self.last_token_time = current_time

        phrase = None

        if self._should_chunk_on_punctuation(token):
            phrase = self._extract_phrase()

        elif self.token_count >= self.config.max_tokens:
            phrase = self._extract_phrase()

        elif (
            time_since_last_token_ms > self.config.pause_threshold_ms
            and self.token_count >= self.config.min_phrase_length
        ):
            phrase = self._extract_phrase()

        return phrase

    def _should_chunk_on_punctuation(self, token: str) -> bool:
        """Check if token ends with chunk-triggering punctuation."""
        stripped = token.strip()
        if not stripped:
            return False
        return any(stripped.endswith(p) for p in self.config.punctuation_markers)

    def _extract_phrase(self) -> Optional[str]:
        """Extract and clear the current buffer."""
        if not self.buffer.strip():
            return None

        phrase = self.buffer.strip()
        self.buffer = ""
        self.token_count = 0

        return phrase

    def flush(self) -> Optional[str]:
        """Flush remaining buffer as final phrase."""
        phrase = self._extract_phrase()
        return phrase

    def reset(self) -> None:
        """Reset chunker state."""
        self.buffer = ""
        self.token_count = 0
        self.last_token_time = time.time()


class StreamingChunker:
    """Advanced chunker that handles partial words and streaming."""

    def __init__(self, config: Optional[ChunkerConfig] = None):
        self.config = config or ChunkerConfig()
        self.pending_word = ""
        self.buffer = ""
        self.last_token_time = time.time()
        self.token_count = 0

    def add_token(self, token: str) -> List[str]:
        """
        Add a token and return any complete phrases.

        Returns:
            List of complete phrases (usually 0 or 1)
        """
        phrases = []

        if self.pending_word:
            token = self.pending_word + token
            self.pending_word = ""

        self.buffer += token
        self.token_count += 1
        current_time = time.time()
        time_since_last_token_ms = (current_time - self.last_token_time) * 1000
        self.last_token_time = current_time

        while len(self.buffer) > 1:
            phrase = self._try_extract_phrase()
            if phrase:
                phrases.append(phrase)
            else:
                break

        if self._might_be_incomplete_word(self.buffer):
            self.pending_word = self.buffer
            self.buffer = ""

        if self.token_count >= self.config.max_tokens:
            phrase = self._force_extract_phrase()
            if phrase:
                phrases.append(phrase)

        if (
            time_since_last_token_ms > self.config.pause_threshold_ms
            and self.token_count >= self.config.min_phrase_length
        ):
            phrase = self._force_extract_phrase()
            if phrase:
                phrases.append(phrase)

        return phrases

    def _try_extract_phrase(self) -> Optional[str]:
        """Try to extract a complete phrase."""
        for punct in self.config.punctuation_markers:
            idx = self.buffer.find(punct)
            if idx >= 0:
                phrase = self.buffer[: idx + 1].strip()
                self.buffer = self.buffer[idx + 1 :]
                self.token_count = max(0, self.token_count - len(phrase.split()))
                return phrase
        return None

    def _force_extract_phrase(self) -> Optional[str]:
        """Force extract whatever is in the buffer."""
        if not self.buffer.strip():
            return None

        phrase = self.buffer.strip()
        self.buffer = ""
        self.token_count = 0
        self.pending_word = ""

        return phrase

    def _might_be_incomplete_word(self, text: str) -> bool:
        """Check if text might be an incomplete word."""
        return len(text) > 0 and not text[-1].isspace()

    def flush(self) -> str:
        """Flush remaining buffer."""
        result = (
            self.pending_word + " " + self.buffer if self.pending_word else self.buffer
        )
        self.reset()
        return result.strip()

    def reset(self) -> None:
        """Reset chunker state."""
        self.pending_word = ""
        self.buffer = ""
        self.token_count = 0
        self.last_token_time = time.time()
