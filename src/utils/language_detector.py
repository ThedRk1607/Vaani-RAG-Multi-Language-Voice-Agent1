"""
Vaani RAG — Language Detector
Supports: Hindi, English, Hinglish, Bengali, Marathi, Bhojpuri
"""

from dataclasses import dataclass
from langdetect import detect, DetectorFactory
from src.utils.logger import logger

# Consistent results ke liye seed fix karo
DetectorFactory.seed = 42


@dataclass
class LanguageResult:
    """Single language ka complete config."""
    code: str
    name: str
    tts_code: str            # gTTS ke liye
    prompt_instruction: str  # LLM ko batao kis language mein jawab do


# Supported languages ka config
LANGUAGE_CONFIG: dict[str, LanguageResult] = {
    "en": LanguageResult(
        code="en",
        name="English",
        tts_code="en",
        prompt_instruction="Respond in clear English.",
    ),
    "hi": LanguageResult(
        code="hi",
        name="Hindi",
        tts_code="hi",
        prompt_instruction="Respond in Hindi (Devanagari script).",
    ),
    "hi-en": LanguageResult(
        code="hi-en",
        name="Hinglish",
        tts_code="hi",
        prompt_instruction="Respond in Hinglish — mix of Hindi and English in Roman script.",
    ),
    "bn": LanguageResult(
        code="bn",
        name="Bengali",
        tts_code="bn",
        prompt_instruction="Respond in Bengali (বাংলা script).",
    ),
    "mr": LanguageResult(
        code="mr",
        name="Marathi",
        tts_code="mr",
        prompt_instruction="Respond in Marathi (मराठी script).",
    ),
    "bho": LanguageResult(
        code="bho",
        name="Bhojpuri",
        tts_code="hi",  # gTTS mein Bhojpuri nahi — Hindi closest hai
        prompt_instruction="Respond in Bhojpuri language.",
    ),
}

# Hinglish detect karne ke liye common Hindi Roman script words
HINGLISH_KEYWORDS = {
    "kya", "hai", "hain", "kaise", "kaisa", "kaisi", "mujhe", "mera", "meri", "mere",
    "naam", "tumhe", "tumhara", "tumhari", "hoga", "hogi", "nahi", "acha", "achha",
    "theek", "batao", "bataiye", "bolo", "karo", "karna", "karein", "bhi", "bahut",
    "yaar", "bhai", "matlab", "samjho", "dekho", "suno", "chahiye", "haan", "kyun",
    "kab", "kahan", "konsa", "kaun", "kaunsa", "kisne", "iski", "iska", "iske",
}


class LanguageDetector:
    """
    Text se language detect karta hai.

    Flow:
    Text → Hinglish check → langdetect → LanguageResult
    """

    def detect(self, text: str, override: str = "auto") -> LanguageResult:
        """
        Language detect karo text se.

        Args:
            text: User ka input text
            override: Manual language select ('auto' = auto detect)

        Returns:
            LanguageResult — language ka complete config
        """
        # User ne manually language select ki hai
        if override != "auto" and override in LANGUAGE_CONFIG:
            logger.info(f"Language manually set: {override}")
            return LANGUAGE_CONFIG[override]

        try:
            # Check for Indic scripts (Devanagari, Bengali, Marathi)
            has_indic_script = any(
                0x0900 <= ord(c) <= 0x097F or 0x0980 <= ord(c) <= 0x09FF for c in text
            )

            # Pehle Hinglish check karo (Roman script Hindi)
            if not has_indic_script and self._is_hinglish(text):
                logger.info("Detected: Hinglish")
                return LANGUAGE_CONFIG["hi-en"]

            # Agar short Latin text hai bina Hinglish ke, default to English
            if not has_indic_script and len(text.strip().split()) <= 3 and all(ord(c) < 128 for c in text):
                logger.info("Short Latin query → Defaulting to English")
                return LANGUAGE_CONFIG["en"]

            # langdetect se detect karo
            detected = detect(text)
            logger.info(f"Auto-detected language: {detected}")

            # Supported language hai?
            if detected in LANGUAGE_CONFIG:
                return LANGUAGE_CONFIG[detected]

            # Fallback mapping
            fallback_map = {
                "ur": "hi",   # Urdu → Hindi (similar)
                "ne": "hi",   # Nepali → Hindi
                "gu": "hi",   # Gujarati → Hindi fallback
            }

            mapped = fallback_map.get(detected, "en")
            logger.warning(
                f"Unsupported language '{detected}' → falling back to '{mapped}'"
            )
            return LANGUAGE_CONFIG[mapped]

        except Exception as e:
            logger.error(f"Language detection failed: {e} → defaulting to English")
            return LANGUAGE_CONFIG["en"]

    def _is_hinglish(self, text: str) -> bool:
        """
        Check karo ki text Hinglish hai ya nahi.

        Logic:
        At least one distinct Roman Hindi word present, and ratio >= 0.2
        or at least 2 distinct Roman Hindi words.
        """
        words = set(text.lower().split())

        if not words:
            return False

        hinglish_hits = words.intersection(HINGLISH_KEYWORDS)
        if not hinglish_hits:
            return False

        ratio = len(hinglish_hits) / len(words)
        logger.debug(f"Hinglish ratio: {ratio:.2f} ({len(hinglish_hits)}/{len(words)} words)")

        return ratio >= 0.2 or len(hinglish_hits) >= 2

    def get_all_languages(self) -> list[dict]:
        """
        UI ke liye saari languages return karo.
        Streamlit dropdown mein use hoga.
        """
        return [
            {"code": code, "name": lang.name}
            for code, lang in LANGUAGE_CONFIG.items()
        ]


__all__ = ["LanguageDetector", "LanguageResult", "LANGUAGE_CONFIG"]
