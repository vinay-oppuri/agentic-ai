# infra/key_manager.py
from itertools import cycle
from loguru import logger
from app.config import settings


class KeyManager:
    _cycle = None
    keys = []     # <-- NEW: store explicit list of keys

    @classmethod
    def _init(cls):
        if cls._cycle:
            return

        raw = (settings.google_keys or settings.google_api_key or "").strip()

        if not raw:
            logger.error(
                "KeyManager: No Google keys found in settings.google_keys or settings.google_api_key"
            )
            raise RuntimeError("No Google API keys available")

        cls.keys = [k.strip() for k in raw.split(",") if k.strip()]

        if not cls.keys:
            logger.error("KeyManager: parsed zero keys")
            raise RuntimeError("No Google API keys available")

        cls._cycle = cycle(cls.keys)

        logger.info(f"KeyManager: initialized with {len(cls.keys)} keys")

    @classmethod
    def next_key(cls) -> str:
        cls._init()
        return next(cls._cycle)
