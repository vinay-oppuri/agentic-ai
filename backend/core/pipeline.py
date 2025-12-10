# core/pipeline.py
"""
core/pipeline.py
----------------
Unified pipeline entrypoint around the LangGraph agent_graph.

Used by FastAPI route to:
 - Run the graph
 - Persist useful artifacts
 - Optionally save into Neon DB
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from graph.graph_builder import agent_graph
from core.types import Document
from infra.memory_store import save_text, save_json
from infra.db import save_pipeline_result


DATA_DIR = Path("data")
RAW_DOCS_DIR = DATA_DIR / "raw_docs"
RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)


async def run_pipeline(user_query: str) -> Dict[str, Any]:
    """
    Async pipeline entrypoint.

    Returns:
        {
          "status": "success" | "error",
          "intent": ...,
          "summary": ...,
          "final_report": ...,
          "agent_outputs": ...,
          "retrieved_docs": ...,
          "state": ...
        }
    """
    logger.info("🚀 [PIPELINE] Starting pipeline for query: %s", user_query)

    try:
        initial_state = {"user_input": user_query}

        final_state = await agent_graph.ainvoke(initial_state)
        if not final_state:
            raise RuntimeError("Graph returned empty state")

        intent = final_state.get("intent")
        summary = final_state.get("summary")
        final_report = final_state.get("final_report")
        agent_outputs = final_state.get("agent_outputs", [])
        retrieved_docs = final_state.get("retrieved_docs", [])

        # Convert Document objects → JSONable dicts
        raw_docs_json = []
        for d in retrieved_docs:
            if isinstance(d, Document):
                raw_docs_json.append(
                    {
                        "page_content": d.page_content,
                        "metadata": d.metadata,
                    }
                )
            elif isinstance(d, dict):
                raw_docs_json.append(d)

        # Save raw docs file for debugging / offline analysis
        raw_docs_path = RAW_DOCS_DIR / "raw_docs.json"
        raw_docs_path.write_text(
            json.dumps(raw_docs_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Save final report & state into memory_store
        if final_report:
            save_text("final_report", final_report)
        save_json("last_intent", intent or {})
        save_json("last_agent_outputs", agent_outputs)
        save_json("last_state", final_state)

        # Save to Neon DB
        try:
            if final_report is not None:
                await save_pipeline_result(
                    idea=user_query,
                    intent=intent or {},
                    strategy={"agent_outputs": agent_outputs},
                    report_md=final_report,
                )
        except Exception as e:
            logger.error(f"⚠️ Failed to persist pipeline result in Neon: {e}")

        result: Dict[str, Any] = {
            "status": "success",
            "intent": intent,
            "summary": summary,
            "final_report": final_report,
            "agent_outputs": agent_outputs,
            "retrieved_docs": raw_docs_json,
            "state": final_state,
        }

        logger.info("✅ [PIPELINE] Completed successfully.")
        return result

    except Exception as e:
        logger.error(f"❌ [PIPELINE] Failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }
