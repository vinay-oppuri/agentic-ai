from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.chat_bot import answer_query, ChatMemory
from supabase import create_client
import os

app = FastAPI(title="Agentic Research + Chat API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase/Neon setup (replace with your db client) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class ChatRequest(BaseModel):
    query: str
    user_id: str

@app.post("/api/chat")
async def chat_with_bot(req: ChatRequest):
    memory = ChatMemory(req.user_id)
    result = answer_query(req.user_id, req.query, memory)

    # Save to DB
    supabase.table("chats").insert({
        "user_id": req.user_id,
        "query": req.query,
        "response": result["answer"],
    }).execute()

    return {"reply": result["answer"], "retrieved_docs": result.get("retrieved_docs", 0)}

@app.get("/api/get-chats/{user_id}")
async def get_chats(user_id: str):
    res = supabase.table("chats").select("*").eq("user_id", user_id).order("created_at").execute()
    return {"chats": res.data}