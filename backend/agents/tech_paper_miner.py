# agents/tech_paper_miner.py
"""
TechPaperMiner Agent
--------------------
Summarizes technical & research landscape for a given query.

Shaped to feed into report_builder.format_tech_summary().
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

    logger.warning("TechPaperMiner: Could not parse JSON, returning empty list.")
    return []


async def tech_paper_miner_agent(query: str) -> List[Dict[str, Any]]:
    """
    Main agent function.

    Returns:
        List of objects like:
        {
          "title": str,
          "authors": [str, ...],
          "source_url": str,
          "summary": str,
          "key_findings": [str, ...]
        }
    """
    prompt = f"""
You are a Technical Research Analyst.

For the following startup idea/problem:

\"\"\"{query}\"\"\"

Identify relevant research or technical directions (they can be based on
real or plausible existing work). Summarize state of the art.

Return ONLY valid JSON in this exact format:

[
  {{
    "title": "Paper or research topic title",
    "authors": ["Author 1", "Author 2"],
    "source_url": "https://... or 'N/A'",
    "summary": "2–4 sentence description of what it does.",
    "key_findings": [
      "key insight 1",
      "key insight 2"
    ]
  }},
  ...
]
"""

    logger.info("📚 [TechPaperMiner] Calling LLM...")
    raw = await llm_generate(prompt)
    papers = _safe_json_list(raw)
    logger.info(f"✅ [TechPaperMiner] Parsed {len(papers)} research items.")
    return papers
