# infra/genai_client.py
import os
import time
from loguru import logger
from fastapi.concurrency import run_in_threadpool
from google import genai
from infra.key_manager import KeyManager
from app.config import settings


class GenAIClient:
    """
    Enhanced Google GenAI wrapper with:
    - multi-key rotation
    - exponential backoff
    - retry limits
    - safe fallback
    """

    # ------------------------------
    # Retry configuration
    # ------------------------------
    max_retries_per_key = 3         # retry a single key this many times
    max_total_retries = 15          # hard global cap
    initial_backoff = 1.0           # seconds
    max_backoff = 12                # cap for exponential backoff
    soft_fail = True                # do not crash pipeline on quota error

    @staticmethod
    def _make_client_for_key(api_key: str):
        os.environ["GOOGLE_API_KEY"] = api_key  # keep compatibility with older libs
        return genai.Client(api_key=api_key)

    @classmethod
    def _backoff(cls, attempt: int):
        delay = min(cls.initial_backoff * (2 ** attempt), cls.max_backoff)
        logger.warning(f"⏳ Backoff {delay:.1f}s before retry…")
        time.sleep(delay)

    # ---------------------------------------------------------------------
    # LLM CALL
    # ---------------------------------------------------------------------
    @classmethod
    def generate(cls, model: str, prompt: str):
        """
        Robust synchronous LLM call:
        - rotates keys via KeyManager
        - retries each key
        - retries globally
        - exponential backoff
        - optional soft-fail fallback
        """
        failures = 0

        for _ in range(len(KeyManager.keys) * cls.max_retries_per_key):
            key = KeyManager.next_key()
            client = cls._make_client_for_key(key)

            for attempt in range(cls.max_retries_per_key):
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )

                    text = (
                        getattr(resp, "text", None)
                        or getattr(resp, "content", None)
                        or str(resp)
                    )
                    return text

                except Exception as e:
                    failures += 1
                    logger.warning(
                        f"⚠️ LLM error (key={key[:6]}…, attempt={attempt+1}): {e}"
                    )

                    # stop if too many global failures
                    if failures >= cls.max_total_retries:
                        logger.error(
                            f"❌ LLM hard-stop: exceeded global retry limit ({cls.max_total_retries})."
                        )

                        if cls.soft_fail:
                            return (
                                "⚠️ LLM Quota Exhausted — returning fallback output. "
                                "Try again later or upgrade Gemini quota."
                            )
                        raise e

                    cls._backoff(attempt)

            logger.warning(f"🔁 Key exhausted → Switching key…")

        # if loop exits without return:
        if cls.soft_fail:
            logger.error("💥 All keys failed — returning fallback summary.")
            return (
                "⚠️ LLM Quota Exhausted — All API keys failed. "
                "Please retry later."
            )

        raise RuntimeError("All Gemini API keys failed.")

    @classmethod
    async def generate_async(cls, model: str, prompt: str):
        """Async wrapper for FastAPI."""
        return await run_in_threadpool(cls.generate, model, prompt)

    # ---------------------------------------------------------------------
    # EMBEDDING CALL
    # ---------------------------------------------------------------------
    @classmethod
    def embed(cls, texts, model="text-embedding-004", dim=3072, task="RETRIEVAL_DOCUMENT"):
        """
        Robust embedding call: safe fallback for errors.
        """
        key = KeyManager.next_key()
        client = cls._make_client_for_key(key)

        try:
            resp = client.models.embed_content(
                model=model,
                contents=texts,
                config=genai.types.EmbedContentConfig(
                    output_dimensionality=dim,
                    task_type=task,
                ),
            )
            return [e.values for e in resp.embeddings]

        except Exception as e:
            logger.error(f"❌ Embedding failed (key={key[:6]}…): {e}")
            return [[] for _ in texts]

    @classmethod
    async def embed_async(cls, texts, **kwargs):
        return await run_in_threadpool(cls.embed, texts, **kwargs)