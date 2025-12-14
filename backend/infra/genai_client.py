# infra/genai_client.py
"""
GenAI Client Module
-------------------
A robust wrapper around the Google GenAI SDK.
Features:
- Exponential backoff for rate limits.
- Safe fallbacks for quota exhaustion.
- Consistent embedding dimensions.
- Direct API key support.
"""

import os
import time
from typing import List, Optional

from loguru import logger
from fastapi.concurrency import run_in_threadpool
from google import genai
from google.genai import types

from app.config import settings


class GenAIClient:
    """
    Enhanced Google GenAI wrapper.
    """

    # Retry Configuration
    MAX_RETRIES = 2
    INITIAL_BACKOFF = 4.0  # seconds
    MAX_BACKOFF = 20.0     # seconds

    @staticmethod
    def _make_client(api_key: Optional[str] = None) -> genai.Client:
        """Creates a GenAI client instance."""
        key = api_key or settings.google_api_key
        if not key:
            raise ValueError("No Google API key provided.")
        
        # Set env var for compatibility
        os.environ["GOOGLE_API_KEY"] = key
        return genai.Client(api_key=key)

    @classmethod
    def _backoff(cls, attempt: int) -> None:
        """Sleeps for an exponential backoff duration."""
        delay = min(cls.INITIAL_BACKOFF * (2 ** attempt), cls.MAX_BACKOFF)
        logger.warning(f"⏳ Backoff {delay:.1f}s before retry...")
        time.sleep(delay)

    @classmethod
    def generate(cls, model: str, prompt: str, api_key: Optional[str] = None, **kwargs) -> str:
        """
        Generates content using the specified model and prompt.
        
        Args:
            model (str): Model name (e.g., "gemini-2.5-flash").
            prompt (str): The input prompt.
            api_key (str, optional): Specific API key to use.
            **kwargs: Additional config parameters (temperature, max_output_tokens, etc.)
            
        Returns:
            str: The generated text, or a fallback message if retries fail.
        """
        client = cls._make_client(api_key)

        for attempt in range(cls.MAX_RETRIES):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**kwargs)
                )
                
                # Extract text safely
                text = (
                    getattr(resp, "text", None)
                    or getattr(resp, "content", None)
                    or str(resp)
                )
                return text

            except Exception as e:
                logger.warning(f"⚠️ LLM error (attempt={attempt+1}): {e}")
                if attempt < cls.MAX_RETRIES - 1:
                    cls._backoff(attempt)
                else:
                    logger.error("❌ LLM failed after retries.")
                    return "⚠️ LLM Error — Request failed."

        return "⚠️ LLM Error — Request failed."

    @classmethod
    async def generate_async(cls, model: str, prompt: str, api_key: Optional[str] = None, **kwargs) -> str:
        """Async wrapper for generate."""
        return await run_in_threadpool(cls.generate, model, prompt, api_key, **kwargs)

    @classmethod
    def embed(cls, texts: List[str], model: str = "text-embedding-004", dim: int = 768, task: str = "RETRIEVAL_DOCUMENT", api_key: Optional[str] = None) -> List[List[float]]:
        """
        Generates embeddings for a list of texts.
        """
        client = cls._make_client(api_key)

        for attempt in range(cls.MAX_RETRIES):
            try:
                resp = client.models.embed_content(
                    model=model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=dim,
                        task_type=task,
                    ),
                )
                return [e.values for e in resp.embeddings]

            except Exception as e:
                logger.warning(f"⚠️ Embedding error (attempt={attempt+1}): {e}")
                if attempt < cls.MAX_RETRIES - 1:
                    cls._backoff(attempt)
                else:
                    logger.error("❌ Embedding failed after retries.")
                    return [[] for _ in texts]
        
        return [[] for _ in texts]

    @classmethod
    async def embed_async(cls, texts: List[str], **kwargs) -> List[List[float]]:
        """Async wrapper for embed."""
        return await run_in_threadpool(cls.embed, texts, **kwargs)