"""
Vaani RAG — Logger
Centralized logging setup using Loguru.
"""

import sys
from pathlib import Path
import os
from loguru import logger


def setup_logger() -> None:
    """Configure loguru logger for the application."""

    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Remove default handler
    logger.remove()

    # Console handler — colored & readable
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> — "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
    )

    # File handler — full details saved to disk
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "vaani_rag.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        level="DEBUG",
        rotation="10 MB",   # Naya file 10MB ke baad
        retention="7 days", # 7 din purane logs rakhta hai
        compression="zip",  # Purane logs compress karta hai
    )


# App start hote hi setup ho jaata hai
setup_logger()


__all__ = ["logger"]
