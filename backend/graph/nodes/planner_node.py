# graph/nodes/planner_node.py

import json
from loguru import logger

from graph.state import AgentState
from infra.genai_client import GenAIClient


async def planner_node(state: AgentState) -> AgentState:
    """
    Dynamic Task Planner Node
    -------------------------
    Converts parsed intent → task plan (tasks + suggested agents).

    Works with Gemini native SDK (no LangChain).
    """

    user_input = state.get("user_input", "")
    intent = state.get("intent", {})

    logger.info("[PlannerNode] 🧠 Creating dynamic task plan...")

    # ----------------------------
    # BUILD PROMPT
    # ----------------------------
    prompt = f"""
You are an intelligent **Dynamic Task Planner** for an Agentic Startup Research Assistant.

Given the parsed startup intent:
{json.dumps(intent, indent=2)}

Generate a **pure JSON** object with the following fields:

- research_goal: short summary of what needs to be researched
- suggested_agents: list of agents to invoke next 
      (choose from: ["CompetitorScout", "TechPaperMiner", "TrendScraper"])

- tasks: a list of max 4 objects with:
      id, title, description, priority, depends_on, assigned_agent

- expected_outputs: list of expected artifacts (summaries, datasets, etc.)

- reasoning_notes: why these tasks were chosen

⚠️ RULES:
- Return ONLY JSON.
- No explanations, no markdown, no code fences.
"""

    # ----------------------------
    # CALL GEMINI (async wrapper)
    # ----------------------------
    raw = await GenAIClient.generate_async(
        model="gemini-2.5-flash",
        prompt=prompt,
    )

    plan = _safe_parse_plan(raw, intent)

    # Write back to graph state
    return {
        **state,
        "plan": plan,
    }


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def _safe_parse_plan(raw: str, intent: dict):
    """
    Cleans and loads JSON. Falls back to deterministic plan if needed.
    """
    try:
        clean = _extract_json(raw)
        return json.loads(clean)
    except Exception as e:
        logger.warning(f"[PlannerNode] ⚠️ Failed JSON parse: {e}. Using fallback plan.")
        return _fallback_plan(intent)


def _extract_json(text: str) -> str:
    """Extract JSON object from messy LLM output."""
    text = text.strip()

    # Remove ```json fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        return text[start:end + 1]

    raise ValueError("No JSON object found in LLM output")


def _fallback_plan(intent: dict):
    """
    Deterministic fallback plan when Gemini fails or quota exceeded.
    """

    tech_keywords_raw = intent.get("tech_keywords", [])
    if isinstance(tech_keywords_raw, str):
        tech_keywords = [w.strip() for w in tech_keywords_raw.split(",")]
    else:
        tech_keywords = tech_keywords_raw

    agents = []

    if any(k.lower() in [t.lower() for t in tech_keywords] for k in ["AI", "Machine Learning", "NLP", "LLM"]):
        agents.append("TechPaperMiner")

    if "competitor" in intent.get("raw_query", "").lower():
        agents.append("CompetitorScout")

    agents.append("TrendScraper")

    tasks = []
    for i, ag in enumerate(agents, 1):
        tasks.append({
            "id": i,
            "title": f"{ag} Task",
            "description": f"Execute {ag} to collect insights relevant to the user query.",
            "priority": i,
            "depends_on": [],
            "assigned_agent": ag,
        })

    return {
        "research_goal": "Generate initial insights on competitors, trends, and technical feasibility.",
        "suggested_agents": agents,
        "tasks": tasks,
        "expected_outputs": ["summaries", "agent_reports", "retrieved_docs"],
        "reasoning_notes": "Fallback rule-based plan used.",
    }