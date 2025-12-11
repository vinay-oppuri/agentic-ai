# core/llm.py
"""
LLM utilities using native Google GenAI (Gemini).
Provides async-friendly wrappers for text generation and embeddings.
"""

from typing import List, Optional
from loguru import logger

from infra.genai_client import GenAIClient
from app.config import settings


# -----------------------------
# Text generation
# -----------------------------

async def llm_generate(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Async wrapper around GenAIClient.generate_async.

    IMPORTANT:
    - We do NOT pass generation_config to SDK (incompatible with google-genai API).
    - Instead, temperature is embedded as a metadata hint inside the prompt.
    """
    model_name = model or settings.gemini_model

    # Hint temperature to LLM (safe + works cross-version)
    prompt_with_hint = f"[temperature={temperature}]\n\n{prompt}"

    logger.debug(f"[LLM] generate model={model_name}, prompt_len={len(prompt)}")

    # Let GenAIClient handle key rotation + error retries
    return await GenAIClient.generate_async(model=model_name, prompt=prompt_with_hint)


# -----------------------------
# Embeddings
# -----------------------------

async def embed_texts(
    texts: List[str],
    model: str = "text-embedding-004",
    dim: int = 3072,
    task: str = "RETRIEVAL_DOCUMENT",
) -> List[List[float]]:
    """
    Async wrapper around GenAIClient.embed_async.
    """
    if not texts:
        return []

    logger.debug(f"[EMB] embedding count={len(texts)}, model={model}")

    # Threadpool wrapper handled internally by embed_async
    return await GenAIClient.embed_async(texts, model=model, dim=dim, task=task)
