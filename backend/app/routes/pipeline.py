# app/routes/pipeline.py
from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas import PipelineRequest, PipelineResponse
from core.pipeline import run_pipeline


router = APIRouter(tags=["pipeline"])


@router.post("/pipeline/run", response_model=PipelineResponse)
async def pipeline_run(req: PipelineRequest):
    """
    Execute the full agentic pipeline for a given query.
    """
    logger.info(f"🌐 [API] /pipeline/run called with query: {req.query!r}")

    result = await run_pipeline(req.query)

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
