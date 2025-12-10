# graph/nodes/intent_node.py
from loguru import logger

from graph.state import AgentState
from core.intent_parser import IntentParser


async def intent_node(state: AgentState) -> AgentState:
    """
    First node: parse user intent into structured metadata.
    """
    user_input = state["user_input"]
    logger.info(f"[IntentNode] Parsing intent for: {user_input!r}")

    parser = IntentParser()
    intent = parser.parse(user_input)

    return {
        **state,
        "intent": intent,
    }
