# core/tools/paper_miner_tool.py
"""
paper_miner_tool.py
-------------------
Wrapper around TechPaperMiner agent.
"""

from typing import Any, Dict

from agents.tech_paper_miner import tech_paper_miner_agent


async def paper_miner_tool(query: str) -> Dict[str, Any]:
    """
    Runs technical paper mining.
    """
    response = await tech_paper_miner_agent(query)
    return {
        "agent": "TechPaperMiner",
        "result": response.get("output_summary", []),
        "raw_docs": response.get("output_raw_docs", [])
    }
