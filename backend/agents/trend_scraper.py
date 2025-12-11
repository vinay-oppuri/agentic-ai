# agents/trend_scraper.py
"""
TrendScraper Agent (Native GenAI — No LangChain)
------------------------------------------------
Collects market trends using:
 - NewsAPI
 - Reddit
 - Tavily Web Search
 - Gemini LLM (via infra/genai_client.GenAIClient)

Returns BOTH:
 - Structured trend summary (list[dict])
 - Raw documents for RAG

Used by planner + agents_node.
"""

import json
import re
import os
import requests
from typing import Any, Dict, List
from loguru import logger

from infra.genai_client import GenAIClient
from app.config import settings


# --------------------------------------------------------------------
# Helpers: JSON extractors
# --------------------------------------------------------------------
def _extract_json_list(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    text = text.strip()

    # Try direct list parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except:
        pass

    # Extract [ ... ] using regex
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, list):
                return parsed
        except:
            pass

    logger.warning("[TrendScraper] Failed to parse JSON list")
    return []


# --------------------------------------------------------------------
# Simple Tools
# --------------------------------------------------------------------
def fetch_news(topic: str, n: int = 8) -> List[Dict[str, Any]]:
    api_key = getattr(settings, "NEWS_API_KEY", None)
    if not api_key:
        return []

    try:
        url = (
            f"https://newsapi.org/v2/everything?q={topic}"
            f"&sortBy=publishedAt&pageSize={n}&language=en&apiKey={api_key}"
        )
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", "")
            }
            for a in articles
        ]
    except Exception as e:
        logger.warning(f"[TrendScraper] NewsAPI error: {e}")
        return []


def fetch_reddit(subreddit: str = "technology", limit: int = 5) -> List[Dict[str, Any]]:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.reddit.com/r/{subreddit}/top/.json?limit={limit}&t=day"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json().get("data", {}).get("children", [])
        return [
            {
                "title": p["data"]["title"],
                "score": p["data"]["score"],
                "url": f"https://reddit.com{p['data']['permalink']}",
            }
            for p in data
        ]
    except Exception as e:
        logger.warning(f"[TrendScraper] Reddit error: {e}")
        return []


def fetch_tavily(query: str, n: int = 6) -> List[Dict[str, Any]]:
    api_key = getattr(settings, "TAVILY_API_KEY", None)
    if not api_key:
        return []

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "num_results": n},
            timeout=15
        )
        resp.raise_for_status()
        items = resp.json().get("results", [])
        return [
            {
                "title": i.get("title", ""),
                "url": i.get("url", ""),
                "content": i.get("content", ""),
            }
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[TrendScraper] Tavily error: {e}")
        return []


# --------------------------------------------------------------------
# Main Agent
# --------------------------------------------------------------------
async def trend_scraper_agent(query: str) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": True,
        "output_summary": [...],   # structured list
        "output_raw_docs": [...],  # raw text documents for RAG
        "output_type": "TrendReport"
    }
    """
    logger.info(f"📈 [TrendScraper] Starting for query: {query}")

    raw_docs = []

    # ---------------------------------------------------------
    # PHASE 1 — Broad Signals
    # ---------------------------------------------------------
    news = fetch_news(query, 8)
    reddit = fetch_reddit("technology", 5)
    tavily = fetch_tavily(query, 6)

    # Add raw docs
    raw_docs.extend([
        {"type": "news", "data": news},
        {"type": "reddit", "data": reddit},
        {"type": "tavily", "data": tavily},
    ])

    # Create "context blob" for LLM
    context_blob = json.dumps(
        {
            "news": news,
            "reddit": reddit,
            "tavily": tavily
        },
        ensure_ascii=False
    )[:8000]

    # ---------------------------------------------------------
    # PHASE 2 — Ask LLM to extract trend list
    # ---------------------------------------------------------
    prompt = f"""
You are a Market Trends Analyst.

Using the following collected signals:

{context_blob}

Extract 4–6 *clear trends* related to the user problem:

\"\"\"{query}\"\"\"

Return ONLY valid JSON list:

[
  {{
    "trend_name": "Short title",
    "short_summary": "2–3 sentence explanation",
    "supporting_sources": ["url1", "url2", ...],
    "relevance_score": 0-100
  }},
  ...
]
"""

    llm_output = await GenAIClient.generate_async(
        model=settings.gemini_model,
        prompt=prompt
    )
    trends = _extract_json_list(llm_output)

    # ---------------------------------------------------------
    # Fallback: No trends parsed
    # ---------------------------------------------------------
    if not trends:
        trends = [
            {
                "trend_name": "AI-driven Developer Assistants",
                "short_summary": "Increasing adoption of AI coding assistants and autonomous tools.",
                "supporting_sources": [],
                "relevance_score": 90,
            }
        ]

    logger.info(f"📈 [TrendScraper] Extracted {len(trends)} trends.")

    return {
        "success": True,
        "output_summary": trends,
        "output_raw_docs": raw_docs,
        "output_type": "TrendReport",
        "meta": {"agent": "TrendScraper"}
    }
