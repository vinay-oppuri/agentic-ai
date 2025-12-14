# core/pipeline.py
"""
Pipeline Module
---------------
The main entry point for the agentic pipeline.
Orchestrates the flow from user query -> graph execution -> result persistence.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from graph.graph_builder import agent_graph
from core.types import Document
from infra.memory_store import save_text, save_json
from infra.db import save_pipeline_result, is_db_available

# Constants
DATA_DIR = Path("data")
RAW_DOCS_DIR = DATA_DIR / "raw_docs"
RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)


async def run_pipeline(user_query: str) -> Dict[str, Any]:
    """
    Executes the full research pipeline for a given user query.
    
    Args:
        user_query (str): The startup idea or research topic.
        
    Returns:
        Dict[str, Any]: A dictionary containing the pipeline status and results.
    """
    logger.info(f"🚀 [PIPELINE] Starting for query: {user_query}")

    try:
        # 1. Initialize State
        initial_state = {"user_input": user_query}

        # 2. Run Graph
        final_state = await agent_graph.ainvoke(initial_state)
        if not final_state:
            raise RuntimeError("Graph execution returned empty state")

        # 3. Extract Results
        results = _extract_results(final_state)
        
        # 4. Persist Artifacts (Local & DB)
        await _persist_results(user_query, results, final_state)

        logger.info("✅ [PIPELINE] Completed successfully.")
        return {
            "status": "success",
            **results,
            "state": final_state
        }

    except Exception as e:
        logger.error(f"❌ [PIPELINE] Failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def _extract_results(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts key components from the final graph state."""
    retrieved_docs = state.get("retrieved_docs", [])
    
    # Serialize documents
    raw_docs_json = []
    for d in retrieved_docs:
        if isinstance(d, Document):
            raw_docs_json.append({
                "page_content": d.page_content,
                "metadata": d.metadata,
            })
        elif isinstance(d, dict):
            raw_docs_json.append(d)

    return {
        "intent": state.get("intent"),
        "summary": state.get("summary"),
        "final_report": state.get("final_report"),
        "agent_outputs": state.get("agent_outputs", []),
        "retrieved_docs": raw_docs_json,
    }


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts Document objects to dicts for JSON serialization."""
    if isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif hasattr(obj, "dict"): # Pydantic models or Documents with dict() method
        return obj.dict()
    elif hasattr(obj, "to_json"):
        return obj.to_json()
    elif hasattr(obj, "page_content") and hasattr(obj, "metadata"): # Document object
        return {"page_content": obj.page_content, "metadata": obj.metadata}
    else:
        return obj

async def _persist_results(user_query: str, results: Dict[str, Any], final_state: Dict[str, Any]) -> None:
    """Saves pipeline artifacts to disk and database concurrently."""
    
    # Sanitize data for serialization
    sanitized_intent = _sanitize_for_json(results["intent"] or {})
    sanitized_outputs = _sanitize_for_json(results["agent_outputs"])
    sanitized_state = _sanitize_for_json(final_state)

    async def _save_local():
        # Save raw docs locally
        raw_docs_path = RAW_DOCS_DIR / "raw_docs.json"
        try:
            raw_docs_path.write_text(
                json.dumps(results["retrieved_docs"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to save raw docs locally: {e}")

        # Save to memory store
        if results["final_report"]:
            save_text("final_report", results["final_report"])
        
        save_json("last_intent", sanitized_intent)
        save_json("last_agent_outputs", sanitized_outputs)
        save_json("last_state", sanitized_state)

    async def _save_db():
        # Save to Database (if available)
        if results["final_report"] and await is_db_available():
            try:
                await save_pipeline_result(
                    idea=user_query,
                    intent=sanitized_intent,
                    strategy={"agent_outputs": sanitized_outputs},
                    report_md=results["final_report"],
                )
            except Exception as e:
                logger.error(f"⚠️ Failed to persist to DB: {e}")

    # Run concurrently
    import asyncio
    await asyncio.gather(_save_local(), _save_db())
