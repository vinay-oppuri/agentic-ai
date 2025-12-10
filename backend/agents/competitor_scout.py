# agents/competitor_scout.py
"""
CompetitorScout Agent
---------------------
Finds and structures information about competitors for a given product/idea.
Returns a list[dict] shaped for report_builder.format_competitor_summary().
"""

import json
import re
from typing import Any, Dict, List

from loguru import logger

from core.llm import llm_generate


def _safe_json_list(text: str) -> List[Dict[str, Any]]:
    """
    Extract and parse a JSON list from LLM output.
    """
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

    logger.warning("CompetitorScout: Could not parse JSON, returning empty list.")
    return []


async def competitor_scout_agent(query: str) -> List[Dict[str, Any]]:
    """
    Main agent function.

    Returns:
        List of objects like:
        {
          "name": str,
          "domain": str,
          "website": str,
          "summary": str,
          "key_features": [str, ...]
        }
    """
    prompt = f"""
You are a Competitive Intelligence Agent.

For the following startup idea or product description:

\"\"\"{query}\"\"\"

Identify the most relevant DIRECT competitors.

Return ONLY valid JSON in this exact format (no explanation):

[
  {{
    "name": "Competitor Name",
    "domain": "short domain/industry tag (e.g. 'code quality', 'devtools')",
    "website": "https://...",
    "summary": "1–3 line description of what they do.",
    "key_features": [
      "feature 1",
      "feature 2"
    ]
  }},
  ...
]
"""

    logger.info("🤖 [CompetitorScout] Calling LLM...")
    raw = await llm_generate(prompt)
    competitors = _safe_json_list(raw)
    logger.info(f"✅ [CompetitorScout] Parsed {len(competitors)} competitors.")
    return competitors
