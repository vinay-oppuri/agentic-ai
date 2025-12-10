# core/tools/trend_scraper_tool.py
"""
trend_scraper_tool.py
---------------------
Thin wrapper around TrendsScraper agent.
"""

from typing import Any, Dict

from agents.trend_scraper import trend_scraper_agent


async def trend_scraper_tool(query: str) -> Dict[str, Any]:
    """
    Runs trends scraping for the given query.

    Returns:
        {
          "agent": "TrendsScraper",
          "result": <list of trend dicts>
        }
    """
    trends = await trend_scraper_agent(query)
    return {
        "agent": "TrendsScraper",
        "result": trends,
    }
