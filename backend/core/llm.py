# core/llm.py
"""
LLM utilities using native Google GenAI (Gemini).
Provides async-friendly wrappers for text generation and embeddings.
"""

import asyncio
from functools import partial
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
    Async wrapper around GenAIClient.generate().
    Offloads blocking HTTP call to a thread pool.
    """
    model_name = model or settings.gemini_model

    loop = asyncio.get_running_loop()
    func = partial(
        GenAIClient.generate,
        model_name,
        prompt,
        generation_config={"temperature": temperature},
    )

    logger.debug(f"[LLM] Generating with model={model_name}")
    return await loop.run_in_executor(None, func)


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
    Async wrapper around GenAIClient.embed().
    """
    if not texts:
        return []

    loop = asyncio.get_running_loop()
    func = partial(GenAIClient.embed, texts, model=model, dim=dim, task=task)

    logger.debug(f"[EMB] Embedding {len(texts)} texts with model={model}")
    return await loop.run_in_executor(None, func)
