# graph/state.py
from typing import Any, Dict, List, TypedDict, Optional
from core.types import Document


class AgentState(TypedDict, total=False):
    """
    Global LangGraph state.

    Each node reads/writes parts of this dict.
    """
    user_input: str

    intent: Dict[str, Any]
    plan: Any

    agent_outputs: List[Dict[str, Any]]

    retrieved_docs: List[Document]

    summary: str
    final_report: str
