# graph/nodes/rag_node.py
"""
RAG Node
--------
Indexes agent outputs and retrieves relevant context for the final report.
"""

from typing import Any, Dict, List

from loguru import logger

from graph.state import AgentState
from core.rag_manager import VectorStoreManager
from core.types import Document


async def rag_node(state: AgentState) -> AgentState:
    """
    Indexes agent results and retrieves context.
    """
    user_input = state["user_input"]
    agent_outputs = state.get("agent_outputs", [])

    logger.info("📚 [RagNode] Indexing agent outputs...")

    # Prepare docs for indexing
    docs_to_index = []
    for item in agent_outputs:
        agent_name = item.get("agent", "Unknown")
        
        # We index the structured result (summary list)
        # We could also index raw_docs if we wanted deep retrieval
        result_content = str(item.get("result", ""))
        
        docs_to_index.append({
            "page_content": result_content,
            "metadata": {"agent": agent_name}
        })

        # Also index raw docs if available (optional, might be too much noise)
        # For now, let's stick to the summary results as they are high-value

    manager = VectorStoreManager()
    
    # Clear previous run's data (ephemeral RAG for this session)
    # In a real app, we might use session IDs
    await manager.clear_store()
    await manager.add_documents(docs_to_index)

    logger.info(f"🔍 [RagNode] Retrieving context for: {user_input}")
    retrieved_docs = await manager.search(user_input, k=6)

    return {
        **state,
        "retrieved_docs": retrieved_docs,
    }
