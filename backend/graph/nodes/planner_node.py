# graph/nodes/planner_node.py
import json
from loguru import logger

from graph.state import AgentState
from core.llm import llm_generate


async def planner_node(state: AgentState) -> AgentState:
    """
    Simple dynamic task planner.

    Uses LLM to create a small list of tasks for downstream agents.
    """
    user_input = state["user_input"]
    intent = state.get("intent", {})

    logger.info("[PlannerNode] Planning tasks...")

    prompt = f"""
You are a task planner for an Agentic Startup Research Assistant.

User query:
{user_input}

Parsed intent (JSON):
{json.dumps(intent, ensure_ascii=False, indent=2)}

Create a small, focused plan of 3–6 tasks for research and strategy.
Return ONLY valid JSON like:

[
  {{
    "id": 1,
    "title": "Short title",
    "description": "What should be done",
    "agent_hints": ["CompetitorScout", "TrendsScraper", "TechPaperMiner"]
  }},
  ...
]
"""

    raw = await llm_generate(prompt, temperature=0.3)
    try:
        plan = json.loads(raw)
        if not isinstance(plan, list):
            raise ValueError("Plan is not a list")
    except Exception:
        logger.warning("[PlannerNode] Failed to parse JSON plan. Falling back to trivial plan.")
        plan = [
            {
                "id": 1,
                "title": "Baseline analysis",
                "description": "Perform competitor, trend, and tech research.",
                "agent_hints": ["CompetitorScout", "TrendsScraper", "TechPaperMiner"],
            }
        ]

    return {
        **state,
        "plan": plan,
    }
