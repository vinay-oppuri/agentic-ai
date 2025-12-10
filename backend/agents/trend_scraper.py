# agents/trend_scraper.py
"""
TrendsScraper Agent
-------------------
Extracts emerging trends, market signals, and supporting sources
for a given domain/problem.
Shaped for report_builder.format_trends_summary().
"""

import json
import re
from typing import Any, Dict, List

from loguru import logger

from core.llm import llm_generate


def _safe_json_list(text: str) -> List[Dict[str, Any]]:
    text = (text or "").strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    logger.warning("TrendsScraper: Could not parse JSON, returning empty list.")
    return []


async def trend_scraper_agent(query: str) -> List[Dict[str, Any]]:
    """
    Main agent function.

    Returns:
        List of objects like:
        {
          "trend_name": str,
          "short_summary": str,
          "supporting_sources": [str, ...]
        }
    """
    prompt = f"""
You are a Market Trends Analyst.

For the following startup idea or domain:

\"\"\"{query}\"\"\"

Identify key trends and signals relevant to this space.

Return ONLY valid JSON in this exact format:

[
  {{
    "trend_name": "Short trend title",
    "short_summary": "2–3 sentence overview of the trend.",
    "supporting_sources": [
      "source or reference 1",
      "source or reference 2"
    ]
  }},
  ...
]
"""

    logger.info("📈 [TrendsScraper] Calling LLM...")
    raw = await llm_generate(prompt)
    trends = _safe_json_list(raw)
    logger.info(f"✅ [TrendsScraper] Parsed {len(trends)} trends.")
    return trends
