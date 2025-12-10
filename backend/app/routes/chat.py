from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse
from graph.graph_builder import agent_graph

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    try:
        initial_state = {"user_input": req.message}
        result_state = await agent_graph.ainvoke(initial_state)

        return ChatResponse(
            intent=result_state.get("intent", "unknown"),
            summary=result_state.get("summary", ""),
            report=result_state.get("final_report", ""),
            debug_state=result_state if req.session_id == "debug" else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
