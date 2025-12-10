# graph/nodes/agent_node.py
from loguru import logger
import asyncio

from graph.state import AgentState
from core.tools.competitor_tool import competitor_tool
from core.tools.trend_scraper_tool import trend_scraper_tool
from core.tools.paper_miner_tool import paper_miner_tool


async def agent_node(state: AgentState) -> AgentState:
    """
    Multi-agent node:
      - CompetitorScout
      - TrendsScraper
      - TechPaperMiner
    """
    user_input = state["user_input"]
    plan = state.get("plan")

    logger.info("[AgentNode] Running research agents...")

    # For now, we just pass the original user_input to all tools.
    tasks = [
        competitor_tool(user_input),
        trend_scraper_tool(user_input),
        paper_miner_tool(user_input),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    agent_outputs = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[AgentNode] Agent failed: {r}")
            continue
        agent_outputs.append(r)

    logger.info(f"[AgentNode] Collected outputs from {len(agent_outputs)} agents.")

    return {
        **state,
        "agent_outputs": agent_outputs,
    }
