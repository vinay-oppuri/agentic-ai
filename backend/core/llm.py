# core/llm.py
"""
LLM Module
----------
Provides asynchronous wrappers for text generation and embedding using Google GenAI.
Acts as a bridge between the application core and the infrastructure layer.
"""

from typing import List, Optional

from loguru import logger

from infra.genai_client import GenAIClient
from app.config import settings


async def llm_generate(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Generates text using the LLM.
    
    Args:
        prompt (str): The input prompt.
        model (str, optional): Model name. Defaults to settings.gemini_model.
        temperature (float): Sampling temperature (0.0 to 1.0).
        max_tokens (int, optional): Max output tokens.
        api_key (str, optional): Specific API key to use.
        
    Returns:
        str: The generated text.
    """
    model_name = model or settings.gemini_model

    logger.debug(f"🤖 [LLM] Generating with {model_name} (len={len(prompt)})")

    return await GenAIClient.generate_async(
        model=model_name,
        prompt=prompt,
        temperature=temperature,
        max_output_tokens=max_tokens,
        api_key=api_key
    )


async def embed_texts(
    texts: List[str],
    model: str = "text-embedding-004",
    dim: int = 768,
    task: str = "RETRIEVAL_DOCUMENT",
    api_key: Optional[str] = None,
) -> List[List[float]]:
    """
    Generates embeddings for a list of texts.
    
    Args:
        texts (List[str]): List of strings to embed.
        model (str): Embedding model.
        dim (int): Output dimension.
        task (str): Task type.
        api_key (str, optional): Specific API key to use.
        
    Returns:
        List[List[float]]: List of embedding vectors.
    """
    if not texts:
        return []

    logger.debug(f"🧠 [EMBED] Embedding {len(texts)} texts with {model}")

    return await GenAIClient.embed_async(texts, model=model, dim=dim, task=task, api_key=api_key)
