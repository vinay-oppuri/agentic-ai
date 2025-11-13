"""
chat_bot.py (persistent + context-aware)
----------------------------------------
Conversational RAG chatbot with:
 - Persistent user memory (saved to disk)
 - Context-aware reasoning
 - Hybrid context (RAG + conversation)
"""

import json
import argparse
from loguru import logger
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from core.retriever_selector import RetrieverSelector
from core.summarizer import Summarizer
from core.reranker import Reranker

import psycopg2.extras
from db import get_db_conn


# ===============================================================
# 🧠 Persistent Chat Memory
# ===============================================================
class ChatMemory:
    def __init__(self, user_id="user_1"):
        self.user_id = user_id
        self.history = self._load()

    def _load(self):
        try:
            conn = get_db_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT memory FROM chat_memory WHERE user_id = %s", (self.user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                logger.info(f"💾 No memory found for {self.user_id}, starting new one.")
                return []
            return row["memory"] or []
        except Exception as e:
            logger.error(f"DB load failed: {e}")
            return []

    def _save(self):
        try:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO chat_memory (user_id, memory, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET memory = EXCLUDED.memory, updated_at = NOW()
                """,
                (self.user_id, psycopg2.extras.Json(self.history)),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save chat memory: {e}")

    def add(self, user_query: str, bot_answer: str):
        self.history.append({
            "user": user_query,
            "bot": bot_answer,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def get_context(self):
        recent = self.history[-3:]
        return "\n".join([f"User: {h['user']}\nBot: {h['bot']}" for h in recent]).strip()

    def print_history(self):
        print("\n--- Conversation History ---")
        for h in self.history:
            print(f"🧍 {h['user']}\n🤖 {h['bot']}\n")


# ===============================================================
# 🔍 Core Query Answering
# ===============================================================
def answer_query(user_id: str, query: str, memory: ChatMemory,
                 use_rag=True, rag_k=6) -> Dict[str, any]:
    retriever = RetrieverSelector()
    summarizer = Summarizer()
    reranker = Reranker()

    # 🧠 Combine user query with conversational context
    memory_context = memory.get_context()
    combined_query = (
        f"User question: {query}\n\nConversation context:\n{memory_context}"
        if memory_context else query
    )

    logger.info(f"User '{user_id}' asked: {query}")

    # 🔍 RAG retrieval
    if use_rag:
        docs = retriever.retrieve(combined_query)
        if not docs:
            logger.warning("No docs retrieved, using conversational fallback.")
            summary = summarizer.summarize(query, [])
            if not summary or summary.strip() == "":
                summary = (
                    "I don’t have enough context yet to give a detailed answer, "
                    "but you can try rephrasing or providing more details about your startup idea."
                )
            memory.add(query, summary)
            return {"answer": summary, "retrieved_docs": 0}

        # 🔢 Re-rank docs by relevance
        ranked = reranker.rerank(combined_query, docs, top_k=rag_k)
        contexts = [r["text"] for r in ranked]
    else:
        contexts = []

    # 🧩 Merge retrieved context and memory for summarization
    augmented_context = (
        "\n\n--- Memory Context ---\n" + memory_context if memory_context else ""
    )
    query_with_context = f"{query}\n\nUse the following context:\n{augmented_context}"

    summary = summarizer.summarize(query_with_context, contexts)

    # 💾 Store turn in memory
    memory.add(query, summary)
    return {"answer": summary, "retrieved_docs": len(contexts)}


# ===============================================================
# 🧩 Command-line Chat Interface
# ===============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="user_1", help="User ID for persistent chat")
    parser.add_argument("--query", help="Single query (optional)")
    parser.add_argument("--no-rag", dest="use_rag", action="store_false")
    args = parser.parse_args()

    memory = ChatMemory(args.user)

    if args.query:
        # Single-shot mode
        result = answer_query(args.user, args.query, memory, use_rag=args.use_rag)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Interactive CLI loop
        print("🤖 Chatbot is ready! Type your questions (or 'exit' to quit).")
        while True:
            user_input = input("\n🧍 You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Exiting chatbot. Goodbye!")
                break

            result = answer_query(args.user, user_input, memory, use_rag=True)
            print(f"\n🤖 Bot: {result['answer']}")
