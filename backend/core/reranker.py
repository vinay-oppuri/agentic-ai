# core/reranker.py
"""
Reranker
--------
Re-ranks retrieved documents by semantic relevance to a query
using Gemini with strict JSON output.
"""

import json
import re
from typing import Any, Dict, List

from loguru import logger

from core.llm import llm_generate
from core.types import Document


class Reranker:
    def __init__(self, model: str = None, temperature: float = 0.2):
        from app.config import settings

        self.model = model or settings.gemini_model
        self.temperature = temperature
        logger.info(f"🔄 Reranker initialized with model={self.model}")

    async def rerank(self, query: str, docs: List[Document], top_k: int = 5) -> List[Dict[str, Any]]:
        if not docs:
            logger.warning("No documents provided to rerank.")
            return []

        # Limit # & length to control token usage
        texts = [d.page_content[:600] for d in docs[:10]]

        logger.info(f"🔍 Reranking {len(texts)} docs for query: {query!r}")

        prompt = f"""
You are a relevance ranking system.

Given a user query and a list of text chunks, rank the chunks by relevance.

⚠️ IMPORTANT: Output ONLY valid JSON. No explanation.

Format:
[
  {{ "text": "<chunk text>", "score": <0-100> }},
  ...
]

Query:
{query}

Chunks:
{json.dumps(texts, ensure_ascii=False, indent=2)}
"""

        try:
            raw = await llm_generate(prompt, model=self.model, temperature=self.temperature)
            raw = (raw or "").strip()

            # Try parsing raw as JSON directly
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                # Try extract JSON array using regex
                match = re.search(r"\[.*\]", raw, re.DOTALL)
                if not match:
                    raise ValueError("No JSON array found in model output.")
                parsed = json.loads(match.group(0))

            reranked: List[Dict[str, Any]] = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                score = item.get("score")
                if text is None or score is None:
                    continue
                reranked.append({"text": text, "score": float(score)})

            if not reranked:
                raise ValueError("Empty reranked list after parsing.")

            reranked_sorted = sorted(reranked, key=lambda x: x["score"], reverse=True)
            logger.info("✅ Reranking complete.")
            return reranked_sorted[:top_k]

        except Exception as e:
            logger.error(f"❌ Reranker failed: {e}")
            logger.warning("Returning fallback equal scores.")

            # Fallback → preserve original order with flat score
            return [{"text": d.page_content, "score": 50.0} for d in docs[:top_k]]
