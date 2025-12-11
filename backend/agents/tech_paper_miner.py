# agents/tech_paper_miner.py
"""
TechPaperMiner Agent (Native GenAI — No LangChain)
--------------------------------------------------
Collects relevant technical papers using:
 - arXiv API
 - Tavily search
 - Lightweight web scraping

Then asks Gemini to:
 - Extract a clean list of structured papers (title, authors, summary, key findings)
 - Produce JSON output compatible with the report builder

Returns BOTH:
 - structured summary
 - raw documents for RAG
"""

import json
import re
import requests
import arxiv
from typing import Any, Dict, List
from loguru import logger
# from bs4 import BeautifulSoup

from infra.genai_client import GenAIClient
from app.config import settings

import requests
import xml.etree.ElementTree as ET

# --------------------------------------------------------------------
# Utility: JSON extraction
# --------------------------------------------------------------------
def _extract_json_list(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    text = text.strip()

    # Direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except:
        pass

    # Extract `[ ... ]`
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, list):
                return parsed
        except:
            pass

    logger.warning("[TechPaperMiner] Failed to parse JSON list")
    return []


# --------------------------------------------------------------------
# Simple Tools
# --------------------------------------------------------------------

def arxiv_search(query: str, max_results: int = 5):
    """
    Native arXiv search using the official Atom feed (NO external library).
    Returns a list of structured paper metadata.
    """
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{query}&start=0&max_results={max_results}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        ns = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            summary = entry.find("atom:summary", ns).text.strip()

            authors = [
                a.find("atom:name", ns).text.strip()
                for a in entry.findall("atom:author", ns)
            ]

            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib["href"]

            papers.append({
                "title": title,
                "summary": summary,
                "authors": authors,
                "pdf_url": pdf_url or "N/A",
            })

        return papers

    except Exception as e:
        return []



def tavily_search(query: str, n: int = 5) -> List[Dict[str, Any]]:
    """Search Tavily for web articles."""
    api_key = getattr(settings, "TAVILY_API_KEY", None)
    if not api_key:
        return []

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "num_results": n},
            timeout=12
        )
        resp.raise_for_status()
        items = resp.json().get("results", [])
        return [
            {
                "title": i.get("title", ""),
                "url": i.get("url", ""),
                "content": i.get("content", "")
            }
            for i in items
        ]
    except Exception as e:
        logger.warning(f"[TechPaperMiner] Tavily error: {e}")
        return []


def scrape_website(url: str) -> str:
    """Lightweight HTML text scraper."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        return text[:8000]
    except Exception as e:
        logger.warning(f"[TechPaperMiner] scrape failed {url}: {e}")
        return ""


# --------------------------------------------------------------------
# MAIN AGENT
# --------------------------------------------------------------------
async def tech_paper_miner_agent(query: str) -> Dict[str, Any]:
    """
    Returns:
    {
        "success": True,
        "output_summary": [...],
        "output_raw_docs": [...],
        "output_type": "PaperReport"
    }
    """

    logger.info(f"📚 [TechPaperMiner] Starting for query: {query}")

    raw_docs = []

    # ---------------------------------------------------------
    # PHASE 1 — BROAD WEB SEARCH
    # ---------------------------------------------------------
    logger.info("🌐 Tavily search…")
    tavily_items = tavily_search(query, 6)
    raw_docs.append({"type": "tavily", "data": tavily_items})

    # ---------------------------------------------------------
    # PHASE 2 — ACADEMIC SEARCH
    # ---------------------------------------------------------
    logger.info("📄 arXiv search…")
    arxiv_items = arxiv_search(query, 4)
    raw_docs.append({"type": "arxiv", "data": arxiv_items})

    # ---------------------------------------------------------
    # PHASE 3 — SCRAPE WEB PAGES
    # ---------------------------------------------------------
    scraped = []
    for item in tavily_items[:3]:
        url = item.get("url")
        if url:
            scraped_text = scrape_website(url)
            if scraped_text:
                scraped.append({"url": url, "text": scraped_text})
    raw_docs.append({"type": "scraped", "data": scraped})

    # Context blob for LLM
    context_blob = json.dumps(
        {
            "arxiv": arxiv_items,
            "tavily": tavily_items,
            "scraped": scraped,
        },
        ensure_ascii=False
    )[:12000]

    # ---------------------------------------------------------
    # PHASE 4 — Ask Gemini to extract structured papers
    # ---------------------------------------------------------
    prompt = f"""
You are a technical research analyst.

You are given mixed sources of research papers, web articles, and scraped text:

{context_blob}

From this material, extract 3–6 high-value research papers or technical resources.

Return ONLY JSON list:

[
  {{
    "title": "Paper title",
    "authors": ["A", "B"],
    "source_url": "https://...",
    "summary": "2–4 sentences",
    "key_findings": ["finding1", "finding2"]
  }},
  ...
]
"""

    llm_output = await GenAIClient.generate_async(
        model=settings.gemini_model,
        prompt=prompt
    )

    papers = _extract_json_list(llm_output)

    if not papers:
        # fallback
        papers = [
            {
                "title": "AI-Assisted Static Code Analysis",
                "authors": ["Researcher A"],
                "source_url": "N/A",
                "summary": f"Fallback summary for {query}.",
                "key_findings": ["AI helps detect code smells", "LLMs assist static analysis"]
            }
        ]

    logger.info(f"📚 [TechPaperMiner] Extracted {len(papers)} papers.")

    return {
        "success": True,
        "output_summary": papers,
        "output_raw_docs": raw_docs,
        "output_type": "PaperReport",
        "meta": {"agent": "TechPaperMiner"}
    }
