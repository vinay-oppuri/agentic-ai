"""
infra/genai_client.py
---------------------
Centralized GenAI client wrapper for Gemini LLM + Embeddings.
This is the only place where the Google API client is initialized.
"""

from google import genai
from app.config import settings
from loguru import logger


class GenAIClient:
    _client = None

    @classmethod
    def get_client(cls):
        """Return singleton GenAI client."""
        if cls._client is None:
            logger.info("🔌 Initializing GenAI client...")
            cls._client = genai.Client(api_key=settings.google_api_key)
        return cls._client

    @classmethod
    def generate(cls, model: str, prompt: str, **kwargs):
        client = cls.get_client()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                **kwargs
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"❌ GenAI generation error: {e}")
            return ""

    @classmethod
    def embed(cls, texts, model="text-embedding-004", dim=3072, task="RETRIEVAL_DOCUMENT"):
        client = cls.get_client()
        try:
            resp = client.models.embed_content(
                model=model,
                contents=texts,
                config=genai.types.EmbedContentConfig(
                    output_dimensionality=dim,
                    task_type=task
                )
            )
            return [e.values for e in resp.embeddings]
        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            return [[] for _ in texts]
