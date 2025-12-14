# core/utils.py
"""
Core Utilities
--------------
Shared helper functions for agents and core logic.
Includes:
- JSON extraction from LLM output.
- Web search utilities (Tavily, DuckDuckGo).
- URL normalization.
- Web scraping.
"""

import asyncio
import json
import re
import requests
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, parse_qs, unquote

from loguru import logger


from app.config import settings


# --------------------------------------------------------------------
# JSON Extraction
# --------------------------------------------------------------------

def extract_json_list(text: str) -> List[Dict[str, Any]]:
    """Extracts a JSON list from text (robust to markdown blocks)."""
    if not text:
        return []
    
    # Remove markdown code blocks
    text = re.sub(r"```(?:json)?", "", text)
    text = text.replace("```", "").strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try finding [ ... ]
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Try finding multiple { ... } objects
    objs = re.findall(r"\{.*?\}", text, re.DOTALL)
    if objs:
        try:
            return [json.loads(o) for o in objs]
        except json.JSONDecodeError:
            pass

    logger.warning("⚠️ Failed to extract JSON list from text.")
    return []


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extracts a JSON object from text."""
    if not text:
        return {}
    text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


# --------------------------------------------------------------------
# Web Search & Scraping
# --------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalizes URLs, handling DuckDuckGo redirects and missing schemes."""
    if not url:
        return ""

    if url.startswith("//"):
        url = "https:" + url

    if "duckduckgo.com/l/?" in url and "uddg=" in url:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if "uddg" in qs:
                real_url = unquote(qs["uddg"][0])
                if real_url.startswith("//"):
                    real_url = "https:" + real_url
                if not real_url.startswith("http"):
                    real_url = "https://" + real_url
                return real_url
        except Exception:
            pass

    if not url.startswith("http"):
        url = "https://" + url

    return url


async def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a web search using Tavily (preferred) or DuckDuckGo (fallback).
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()

    def _tavily_search():
        if not settings.tavily_api_key:
            return None
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": settings.tavily_api_key, "query": query, "num_results": num_results},
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [
                {"title": r.get("title", ""), "url": normalize_url(r.get("url", "")), "content": r.get("content", "")}
                for r in results
            ]
        except Exception as e:
            logger.warning(f"⚠️ Tavily search failed: {e}")
            return None

    def _ddg_search():
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AgenticAI/1.0)"}
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            items = []
            for m in re.finditer(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>', resp.text):
                raw_url = m.group(1)
                title = re.sub(r"<.*?>", "", m.group(2))
                items.append({"title": title, "url": normalize_url(raw_url), "content": ""})
                if len(items) >= num_results:
                    break
            return items
        except Exception as e:
            logger.warning(f"⚠️ DuckDuckGo fallback failed: {e}")
            return []

    # 1. Try Tavily
    tavily_results = await loop.run_in_executor(None, _tavily_search)
    if tavily_results:
        return tavily_results

    # 2. Fallback: DuckDuckGo
    return await loop.run_in_executor(None, _ddg_search)


async def scrape_url(url: str, max_chars: int = 8000) -> str:
    """
    Scrapes text content from a URL asynchronously.
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    url = normalize_url(url)

    def _scrape():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text
            
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(" ", strip=True)
            except ImportError:
                # Regex fallback
                text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL)
                text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                
            # Remove null bytes (Postgres incompatibility)
            text = text.replace("\x00", "")
                
            return text[:max_chars]
        except Exception as e:
            logger.warning(f"⚠️ Scraping failed for {url}: {e}")
            return ""

    return await loop.run_in_executor(None, _scrape)
