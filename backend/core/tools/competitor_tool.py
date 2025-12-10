# core/tools/competitor_tool.py
"""
competitor_tool.py
------------------
Thin wrapper around CompetitorScout agent.
Returns a standardized agent result dict used in LangGraph state.
"""

from typing import Any, Dict

from agents.competitor_scout import competitor_scout_agent


async def competitor_tool(query: str) -> Dict[str, Any]:
    """
    Runs competitor scouting for the given query.

    Returns:
        {
          "agent": "CompetitorScout",
          "result": <list of competitor dicts>
        }
    """
    summaries = await competitor_scout_agent(query)
    return {
        "agent": "CompetitorScout",
        "result": summaries,
    }
