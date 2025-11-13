from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.pipeline import run_pipeline
from core.chat_bot import ChatMemory, answer_query
from db import get_db_conn
import psycopg2, psycopg2.extras
from psycopg2 import sql

app = FastAPI(title="Agentic Research API")

# =====================================================
# 🌍 CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-vercel-domain.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# 🏠 Root
# =====================================================
@app.get("/")
def home():
    return {"message": "Agentic Research Backend Running 🚀"}


# =====================================================
# 🚀 Full Research Pipeline
# =====================================================
class QueryRequest(BaseModel):
    query: str


@app.post("/api/run")
async def run_agentic_pipeline(request: QueryRequest):
    try:
        result = run_pipeline(request.query)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        # Extract markdown report (read from file)
        with open("report.md", "r", encoding="utf-8") as f:
            report_md = f.read()

        # ✅ Save both to Neon DB
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reports (idea, result_json, report_md, created_at)
            VALUES (%s, %s, %s, NOW())
            """,
            (request.query, psycopg2.extras.Json(result), report_md),
        )
        conn.commit()
        cur.close()
        conn.close()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# =====================================================
# 💬 Chatbot Endpoint (RAG + Neon DB Save)
# =====================================================
@app.post("/api/chat")
async def chat_with_agent(payload: dict = Body(...)):
    user_id = payload.get("user_id", "user_1")
    query = payload.get("query", "")

    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query'")

    try:
        memory = ChatMemory(user_id)
        result = answer_query(user_id, query, memory, use_rag=True)
        response = result.get("answer", "No response")

        # ✅ Save chat log
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            INSERT INTO chats (user_id, query, response, created_at)
            VALUES (%s, %s, %s, NOW())
            """,
            (user_id, query, response),
        )
        conn.commit()
        cur.close()
        conn.close()

        return {"reply": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# =====================================================
# 📄 Get Reports and Chats
@app.get("/api/get-reports")
async def get_reports():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM reports ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.get("/api/get-chats/{user_id}")
async def get_chats(user_id: str):
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM chats WHERE user_id = %s ORDER BY created_at ASC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"chats": rows}




@app.delete("/api/clear-chats/{user_id}")
async def clear_user_chats(user_id: str):
    """
    🧹 Delete all chats for a given user from Neon DB
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("DELETE FROM chats WHERE user_id = %s;", (user_id,))
        conn.commit()

        cur.close()
        conn.close()
        return {"status": "success", "message": f"Cleared chats for {user_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chats: {str(e)}")
