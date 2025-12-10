from typing import Any, Dict, Optional, List
from pydantic import BaseModel


# -------------------------
# Chat API Schema
# -------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    intent: str
    summary: Optional[str] = None
    report: Optional[str] = None
    debug_state: Optional[Dict[str, Any]] = None


# -------------------------
# Pipeline API Schema
# -------------------------

class PipelineRequest(BaseModel):
    query: str


class PipelineResponse(BaseModel):
    status: str
    intent: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    final_report: Optional[str] = None
    agent_outputs: Optional[List[Dict[str, Any]]] = None
    retrieved_docs: Optional[List[Dict[str, Any]]] = None
    state: Optional[Dict[str, Any]] = None
