# core/tools/competitor_tool.py
"""
competitor_tool.py
------------------
Wrapper around CompetitorScout agent.
"""

from typing import Any, Dict

from agents.competitor_scout import competitor_scout_agent


async def competitor_tool(query: str) -> Dict[str, Any]:
    """
    Runs competitor scouting.
    """
    response = await competitor_scout_agent(query)
    return {
        "agent": "CompetitorScout",
        "result": response.get("output_summary", []),
        "raw_docs": response.get("output_raw_docs", [])
    }
