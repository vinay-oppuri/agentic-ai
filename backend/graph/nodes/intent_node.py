# graph/nodes/intent_node.py
"""
Intent Node
-----------
First step in the pipeline.
Parses the user's natural language query into structured intent metadata.
"""

from loguru import logger

from graph.state import AgentState
from core.intent_parser import IntentParser


async def intent_node(state: AgentState) -> AgentState:
    """
    Executes intent parsing.
    """
    user_input = state["user_input"]
    logger.info(f"🧠 [IntentNode] Parsing: {user_input}")

    parser = IntentParser()
    intent = await parser.parse(user_input)

    return {
        **state,
        "intent": intent,
    }
