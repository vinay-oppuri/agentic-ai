# agents/competitor_scout.py
"""
CompetitorScout Agent (native GenAI, no LangChain)
-------------------------------------------------
Multi-phase competitor research using:
 - native Google GenAI client (infra.genai_client.GenAIClient)
 - simple web search / page fetch helpers
 - structured JSON extraction & fallback logic

Primary exported function:
    async def competitor_scout_agent(query: str) -> List[Dict[str, Any]]
"""

import os
import json
import re
import requests
from typing import Any, Dict, List, Tuple
from loguru import logger
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote

from app.config import settings
from infra.genai_client import GenAIClient


# ============================================================
# URL NORMALIZATION FIX  — REQUIRED
# ============================================================

def normalize_url(url: str) -> str:
    """Fixes DuckDuckGo redirect URLs and missing schemes."""

    if not url:
        return url

    # Add https if URL starts with //
    if url.startswith("//"):
        url = "https:" + url

    # Detect DuckDuckGo redirect wrapper
    if "duckduckgo.com/l/?" in url and "uddg=" in url:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)

            if "uddg" in qs:
                real_url = unquote(qs["uddg"][0])
                # Add https if missing
                if real_url.startswith("//"):
                    real_url = "https:" + real_url
                if real_url.startswith("http"):
                    return real_url
                return "https://" + real_url
        except Exception as e:
            logger.warning(f"[normalize_url] redirect parse error: {e}")

    # If still no protocol, add https://
    if not url.startswith("http"):
        url = "https://" + url

    return url


# ============================================================
# SEARCH TOOL (Tavily first, fallback: DuckDuckGo scrape)
# ============================================================

def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    tavily_key = getattr(settings, "TAVILY_API_KEY", None)

    # ---- TRY TAVILY ----
    if tavily_key:
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_key, "query": query, "num_results": num_results},
                timeout=12,
            )
            resp.raise_for_status()
            results = resp.json().get("results", []) or []

            fixed = []
            for r in results:
                url = normalize_url(r.get("url", ""))
                fixed.append({"title": r.get("title", ""), "url": url})
            return fixed[:num_results]

        except Exception as e:
            logger.warning(f"[web_search] Tavily error: {e}")

    # ---- FALLBACK: DuckDuckGo HTML ----
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CompetitorScout/1.0)"}
        q = query.replace(" ", "+")
        url = f"https://html.duckduckgo.com/html/?q={q}"

        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text

        items = []
        for m in re.finditer(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>', html):
            raw_url = m.group(1)
            url = normalize_url(raw_url)
            title = re.sub(r"<.*?>", "", m.group(2))
            items.append({"title": title, "url": url})

            if len(items) >= num_results:
                break

        return items

    except Exception as e:
        logger.warning(f"[web_search] fallback search failed: {e}")
        return []


# ============================================================
# FETCH PAGE TEXT  — FIXED
# ============================================================

def fetch_page_text(url: str, max_chars: int = 8000) -> str:
    """Fetch HTML → clean text. Now includes URL normalization."""
    try:
        url = normalize_url(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CompetitorScoutBot/2.0; +https://example.com/bot)"
        }

        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()

        text = r.text
        # Clean HTML
        text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]

    except Exception as e:
        logger.warning(f"[fetch_page_text] fetch failed for {url}: {e}")
        return f"Fetch failed: {e}"


# ============================================================
# JSON extraction helpers
# ============================================================

def _extract_json_list(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    m = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    objs = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
    if objs:
        try:
            return [json.loads(o) for o in objs]
        except Exception:
            pass

    logger.debug("[_extract_json_list] failed to parse JSON list.")
    return []


def _extract_json_object(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


# ============================================================
# PROMPTS
# ============================================================

_PROMPT_IDENTIFY = """
You are a methodical competitive intelligence assistant.
Given this product idea, list the top 6 *direct* competitors.
Return ONLY JSON:
[
  {"name":"...", "short_reason":"..."},
  ...
]
"""

_PROMPT_EXTRACT_COMPETITOR = """
You are an analytical assistant. Convert this into a structured JSON object:

Fields:
- name
- domain
- website
- summary
- key_features
- pricing
- target_users
- relevance_score

SNIPPET:
{snippet}

SEARCH RESULTS:
{search_results}

Return ONLY a JSON object.
"""


# ============================================================
# MAIN AGENT
# ============================================================

async def competitor_scout_agent(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    logger.info(f"🔎 CompetitorScout started for: {query}")

    # PHASE 1 — identify candidates
    prompt1 = _PROMPT_IDENTIFY + f"\nProduct idea:\n\"\"\"{query}\"\"\""
    raw_candidates = await GenAIClient.generate_async(settings.gemini_model, prompt1)
    candidates = _extract_json_list(raw_candidates)

    if not candidates:
        logger.warning("LLM returned no candidates, using fallback.")
        candidates = [
            {"name": "Rover", "short_reason": "Pet service marketplace"},
            {"name": "Wag!", "short_reason": "Pet walking & care"},
            {"name": "Lyft", "short_reason": "Pet-friendly ride option"},
        ]

    candidates = candidates[: max(top_k * 2, 6)]
    logger.info(f"Phase 1 → candidate count: {len(candidates)}")

    final_competitors = []

    # PHASE 2 — per-candidate extraction
    for cand in candidates:
        try:
            name = cand.get("name")
            if not name:
                continue

            search_query = f"{name} features pricing service {query}"
            search_hits = web_search(search_query, num_results=5)

            # Normalize URLs
            for hit in search_hits:
                hit["url"] = normalize_url(hit.get("url", ""))

            # Pick first URL
            url = next((x["url"] for x in search_hits if x.get("url")), "")
            snippet = fetch_page_text(url) if url else " | ".join(h["title"] for h in search_hits)

            prompt3 = _PROMPT_EXTRACT_COMPETITOR.format(
                snippet=snippet[:2000],
                search_results=json.dumps(search_hits)[:2000]
            )

            raw_profile = await GenAIClient.generate_async(settings.gemini_model, prompt3)
            profile = _extract_json_object(raw_profile)

            # fallback defaults
            profile.setdefault("name", name)
            profile.setdefault("domain", cand.get("short_reason", ""))
            profile.setdefault("website", url)
            profile.setdefault("summary", cand.get("short_reason", ""))
            profile.setdefault("key_features", profile.get("key_features", []))
            profile.setdefault("pricing", profile.get("pricing", "unknown"))
            profile.setdefault("target_users", profile.get("target_users", "unknown"))

            try:
                rs = int(profile.get("relevance_score", 50))
                profile["relevance_score"] = max(0, min(100, rs))
            except:
                profile["relevance_score"] = 50

            final_competitors.append(profile)
            logger.info(f"[CompetitorScout] Collected profile for: {name}")

            if len(final_competitors) >= top_k:
                break

        except Exception as e:
            logger.exception(f"[CompetitorScout] Error processing {cand}: {e}")

    return final_competitors
