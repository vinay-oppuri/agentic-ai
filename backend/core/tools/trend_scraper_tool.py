# core/tools/trend_scraper_tool.py
"""
trend_scraper_tool.py
---------------------
Wrapper around TrendsScraper agent.
"""

from typing import Any, Dict

from agents.trend_scraper import trend_scraper_agent


async def trend_scraper_tool(query: str) -> Dict[str, Any]:
    """
    Runs trends scraping.
    """
    response = await trend_scraper_agent(query)
    return {
        "agent": "TrendsScraper",
        "result": response.get("output_summary", []),
        "raw_docs": response.get("output_raw_docs", [])
    }
