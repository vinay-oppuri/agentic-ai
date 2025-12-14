# app/routes/pipeline.py
"""
Pipeline Route
--------------
Exposes the main agentic research pipeline via REST API.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas import PipelineRequest, PipelineResponse
from core.pipeline import run_pipeline


router = APIRouter(tags=["pipeline"])


@router.post("/pipeline/run", response_model=PipelineResponse)
async def pipeline_run(req: PipelineRequest):
    """
    Executes the full agentic pipeline for a given query.
    
    - Parses intent
    - Plans research tasks
    - Runs agents (Competitor, Trends, Papers)
    - Retrieves context (RAG)
    - Generates final report
    """
    logger.info(f"🌐 [API] /pipeline/run called with query: {req.query}")

    try:
        result = await run_pipeline(req.query)
    except Exception as e:
        logger.error(f"❌ [API] Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "Pipeline failed"))

    return PipelineResponse(
        status="success",
        intent=result.get("intent"),
        summary=result.get("summary"),
        final_report=result.get("final_report"),
        agent_outputs=result.get("agent_outputs"),
        retrieved_docs=result.get("retrieved_docs"),
        state=result.get("state"),
    )
