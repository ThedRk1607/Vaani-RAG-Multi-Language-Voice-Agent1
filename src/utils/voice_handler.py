"""
Vaani RAG — Voice Handler
Ye file do kaam karti hai:
1. STT (Speech to Text) — faster-whisper use karke
2. TTS (Text to Speech) — gTTS use karke
"""

import io
import tempfile
from pathlib import Path
from dataclasses import dataclass

from gtts import gTTS
from faster_whisper import WhisperModel
from src.utils.logger import logger


@dataclass
class TranscriptionResult:
    """STT ka output — transcribed text aur detected language."""
    text: str
    language: str
    confidence: float


class VoiceHandler:
    """
    Voice input aur output handle karta hai.

    STT Flow:
    Audio bytes → Whisper Model → Transcribed Text

    TTS Flow:
    Text + Language → gTTS → Audio bytes
    """

    # Whisper ke supported language codes
    WHISPER_LANGUAGE_MAP = {
        "hi": "hi",      # Hindi
        "hi-en": "hi",   # Hinglish → Hindi se transcribe
        "en": "en",      # English
        "bn": "bn",      # Bengali
        "mr": "mr",      # Marathi
        "bho": "hi",     # Bhojpuri → Hindi closest
    }

    def __init__(self, model_size: str = "base") -> None:
        """
        VoiceHandler initialize karo.

        Args:
            model_size: Whisper model size
                       'tiny' → fastest, less accurate
                       'base' → balanced (recommended)
                       'small' → more accurate, slower
        """
        self._model: WhisperModel | None = None
        self._model_size = model_size
        logger.info(f"VoiceHandler initialized with model size: {model_size}")

    @property
    def model(self) -> WhisperModel:
        """
        Lazy loading — model sirf tab load hoga jab pehli baar use hoga.
        Startup time save hota hai!
        """
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_size}...")
            self._model = WhisperModel(
                self._model_size,
                device="cpu",        # GPU nahi hai toh CPU use karo
                compute_type="int8", # Memory efficient
            )
            logger.success("Whisper model loaded successfully!")
        return self._model

    def transcribe(
        self,
        audio_bytes: bytes,
        language_code: str = "auto",
    ) -> TranscriptionResult:
        """
        Audio bytes ko text mein convert karo (STT).

        Args:
            audio_bytes: Microphone se aaya raw audio data
            language_code: Language hint dena optional hai

        Returns:
            TranscriptionResult — transcribed text + language + confidence
        """
        try:
            logger.info("Starting audio transcription...")

            # Audio bytes ko temporary file mein save karo
            # Whisper directly bytes accept nahi karta
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            # Language hint set karo
            whisper_lang = None
            if language_code != "auto":
                whisper_lang = self.WHISPER_LANGUAGE_MAP.get(language_code)

            # Whisper se transcribe karo
            segments, info = self.model.transcribe(
                tmp_path,
                language=whisper_lang,
                beam_size=5,
                vad_filter=True,  # Silence automatically remove hoga
            )

            # Segments combine karo
            transcribed_text = " ".join(
                segment.text.strip() for segment in segments
            )

            # Temporary file delete karo
            Path(tmp_path).unlink(missing_ok=True)

            logger.success(
                f"Transcription complete: '{transcribed_text[:50]}...'"
            )

            return TranscriptionResult(
                text=transcribed_text,
                language=info.language,
                confidence=info.language_probability,
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def text_to_speech(
        self,
        text: str,
        language_code: str = "en",
    ) -> bytes:
        """
        Text ko audio mein convert karo (TTS).

        Args:
            text: Jo bolna hai
            language_code: Kis language mein bolna hai

        Returns:
            bytes: MP3 audio data — Streamlit mein play hoga
        """
        try:
            logger.info(f"Generating speech in language: {language_code}")

            # gTTS language code map
            gtts_lang_map = {
                "hi": "hi",
                "hi-en": "hi",   # Hinglish → Hindi TTS
                "en": "en",
                "bn": "bn",
                "mr": "mr",
                "bho": "hi",     # Bhojpuri → Hindi TTS
            }

            gtts_lang = gtts_lang_map.get(language_code, "en")

            # gTTS se audio generate karo
            tts = gTTS(text=text, lang=gtts_lang, slow=False)

            # Audio bytes mein save karo
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.read()

            logger.success(
                f"Speech generated: {len(audio_bytes)} bytes"
            )

            return audio_bytes

        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise


__all__ = ["VoiceHandler", "TranscriptionResult"]
