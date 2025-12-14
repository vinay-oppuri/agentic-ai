# graph/nodes/planner_node.py
"""
Planner Node
------------
Generates a dynamic execution plan based on the parsed intent.
Decides which agents to run and what tasks to perform.
"""

import json
from typing import Any, Dict

from loguru import logger

from graph.state import AgentState
from core.llm import llm_generate
from core.utils import extract_json_object
from app.config import settings


async def planner_node(state: AgentState) -> AgentState:
    """
    Generates a research plan.
    """
    user_input = state.get("user_input", "")
    intent = state.get("intent", {})

    logger.info("🗺️ [PlannerNode] Generating plan...")

    prompt = f"""
    You are an intelligent **Dynamic Task Planner** for an Agentic Startup Research Assistant.
    
    Given the parsed startup intent:
    {json.dumps(intent, indent=2)}
    
    Generate a **pure JSON** object with the following fields:
    
    AVAILABLE AGENTS:
    - CompetitorScout: Finds competitors and analyzes their features.
    - TrendScraper: Finds latest market trends and news.
    - TechPaperMiner: Finds technical papers and academic research.
    
    Return a JSON object with:
    {{
        "plan_steps": ["Step 1...", "Step 2..."],
        "selected_agents": ["AgentName1", "AgentName2"]
    }}
    """

    try:
        response = await llm_generate(prompt, temperature=0.3, max_tokens=1024, api_key=settings.google_key_planner)
        if response.startswith("⚠️"):
            raise ValueError(response)
        plan = json.loads(response)
    except Exception as e:
        logger.warning(f"⚠️ [PlannerNode] Planning failed: {e}. Using fallback.")
        plan = _fallback_plan(intent)

    return {
        **state,
        "plan": plan,
    }


def _fallback_plan(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a deterministic fallback plan."""
    tech_keywords = intent.get("tech_keywords", [])
    
    agents = []
    # Simple heuristics
    if any(k.lower() in str(tech_keywords).lower() for k in ["ai", "ml", "llm"]):
        agents.append("TechPaperMiner")
    
    if "competitor" in intent.get("raw_query", "").lower():
        agents.append("CompetitorScout")
        
    # Always include TrendScraper as fallback
    if not agents:
        agents.append("TrendScraper")
    
    # Ensure TrendScraper is there if list is short
    if "TrendScraper" not in agents:
        agents.append("TrendScraper")

    tasks = []
    for i, ag in enumerate(agents, 1):
        tasks.append({
            "id": i,
            "title": f"{ag} Task",
            "description": f"Execute {ag}",
            "priority": i,
            "assigned_agent": ag,
        })

    return {
        "research_goal": "Fallback research plan.",
        "suggested_agents": agents,
        "tasks": tasks,
        "reasoning_notes": "Fallback used due to planner error."
    }