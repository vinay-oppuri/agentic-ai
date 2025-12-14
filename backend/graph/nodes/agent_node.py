# graph/nodes/agent_node.py
"""
Agent Node
----------
Executes the selected research agents in parallel.
"""

import asyncio
from typing import List

from loguru import logger

from graph.state import AgentState
from core.tools.competitor_tool import competitor_tool
from core.tools.trend_scraper_tool import trend_scraper_tool
from core.tools.paper_miner_tool import paper_miner_tool


async def agent_node(state: AgentState) -> AgentState:
    """
    Runs agents specified in the plan.
    """
    user_input = state["user_input"]
    plan = state.get("plan", {})
    suggested_agents = plan.get("suggested_agents", [])

    logger.info(f"🤖 [AgentNode] Executing agents: {suggested_agents}")

    tasks = []
    if "CompetitorScout" in suggested_agents:
        tasks.append(competitor_tool(user_input))
    if "TrendScraper" in suggested_agents:
        tasks.append(trend_scraper_tool(user_input))
    if "TechPaperMiner" in suggested_agents:
        tasks.append(paper_miner_tool(user_input))

    if not tasks:
        logger.warning("⚠️ [AgentNode] No agents triggered. Defaulting to TrendScraper.")
        tasks.append(trend_scraper_tool(user_input))

    # Run in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    agent_outputs = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"❌ [AgentNode] Agent failed: {r}")
            continue
        agent_outputs.append(r)

    logger.info(f"✅ [AgentNode] Collected {len(agent_outputs)} outputs.")

    return {
        **state,
        "agent_outputs": agent_outputs,
    }
