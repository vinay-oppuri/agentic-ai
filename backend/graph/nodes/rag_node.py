# graph/nodes/rag_node.py
from loguru import logger
from typing import List, Dict, Any

from graph.state import AgentState
from core.rag_manager import VectorStoreManager
from core.types import Document


async def rag_node(state: AgentState) -> AgentState:
    """
    RAG node:
      - Indexes structured agent outputs into Neon vector store
      - Retrieves top-k chunks for the user query
    """
    user_input = state["user_input"]
    agent_outputs: List[Dict[str, Any]] = state.get("agent_outputs", [])

    logger.info("[RagNode] Building temporary index from agent outputs...")

    # Convert agent_outputs into documents
    docs_to_index: List[Dict[str, Any]] = []
    for item in agent_outputs:
        agent_name = item.get("agent", "Unknown")
        result = item.get("result")

        # Store the entire result as JSON string
        content = str(result)
        metadata = {"agent": agent_name}

        docs_to_index.append(
            {
                "page_content": content,
                "metadata": metadata,
            }
        )

    manager = VectorStoreManager()

    # Optional: clear store or keep it cumulative.
    await manager.clear_store()
    await manager.add_documents(docs_to_index)

    logger.info("[RagNode] Querying vector store...")
    retrieved = await manager.search(user_input, k=6)

    logger.info(f"[RagNode] Retrieved {len(retrieved)} RAG docs.")

    # Store as Document objects in state
    retrieved_docs: List[Document] = retrieved

    return {
        **state,
        "retrieved_docs": retrieved_docs,
    }
