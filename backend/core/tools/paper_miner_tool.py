# core/tools/paper_miner_tool.py
"""
paper_miner_tool.py
-------------------
Thin wrapper around TechPaperMiner agent.
"""

from typing import Any, Dict

from agents.tech_paper_miner import tech_paper_miner_agent


async def paper_miner_tool(query: str) -> Dict[str, Any]:
    """
    Runs technical paper mining for the given query.

    Returns:
        {
          "agent": "TechPaperMiner",
          "result": <list of paper dicts>
        }
    """
    papers = await tech_paper_miner_agent(query)
    return {
        "agent": "TechPaperMiner",
        "result": papers,
    }
