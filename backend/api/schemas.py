# api/schemas.py
"""
API Schemas
-----------
Pydantic models for request and response validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# -------------------------
# Chat API
# -------------------------

class ChatRequest(BaseModel):
    """Request model for simple chat endpoint."""
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Response model for simple chat endpoint."""
    intent: str
    summary: Optional[str] = None
    report: Optional[str] = None
    debug_state: Optional[Dict[str, Any]] = None


# -------------------------
# Pipeline API
# -------------------------

class PipelineRequest(BaseModel):
    """Request model for full research pipeline."""
    query: str


class PipelineResponse(BaseModel):
    """Response model for full research pipeline."""
    status: str
    intent: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    final_report: Optional[str] = None
    agent_outputs: Optional[List[Dict[str, Any]]] = None
    retrieved_docs: Optional[List[Dict[str, Any]]] = None
    state: Optional[Dict[str, Any]] = None
