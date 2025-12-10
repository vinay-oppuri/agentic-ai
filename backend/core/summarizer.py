"""
summarizer.py
-------------
Summarizes top-ranked chunks into concise insights using native Google GenAI.
"""

import os
from loguru import logger
from typing import List
from google import genai
from app.config import settings

# Load API key
if settings.google_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key


class Summarizer:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = model
        logger.info(f"✅ Summarizer initialized with native Google GenAI model: {model}")

    async def summarize(self, query: str, contexts: List[str]) -> str:
        if not contexts:
            return "No context found to summarize."

        context_text = "\n\n".join(contexts[:10])
        logger.info(f"🧠 Summarizing {len(contexts)} chunks for query: {query}")

        prompt = f"""
You are a research summarization agent.
Your goal is to synthesize information into a concise and factual answer.

### User Query:
{query}

### Context (Top Retrieved Chunks):
{context_text}

### Instructions:
- Write a clear explanation.
- Focus *only* on what is supported by the provided context.
- 2–3 paragraphs max.
"""

        try:
            response = await self.client.models.generate_content_async(
                model=self.model,
                contents=prompt
            )

            return response.text.strip() if response.text else "No summary generated."

        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return "Failed to summarize context."
        

async def summarize_docs(docs):
    """Summarize a list of LangChain Documents using native Google GenAI."""
    from google import genai

    if not docs:
        return ""

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    text = "\n\n".join(d.page_content[:2000] for d in docs)

    prompt = f"""
You are a concise research summarizer.

Summarize the following content into clear bullet points:

CONTENT:
{text}
"""

    try:
        resp = await client.models.generate_content_async(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return resp.text.strip() if resp.text else ""
    except Exception as e:
        print("Summarizer error:", e)
        return ""



# For local manual test
if __name__ == "__main__":
    import asyncio
    from core.reranker import Reranker
    from core.retriever_selector import RetrieverSelector

    async def test():
        query = "Emerging AI trends for 2025 in developer tools"
        retriever = RetrieverSelector()
        reranker = Reranker()
        summarizer = Summarizer()

        docs = retriever.retrieve(query)
        ranked = reranker.rerank(query, docs)
        contexts = [r["text"] for r in ranked]

        summary = await summarizer.summarize(query, contexts)
        print("\n--- FINAL SUMMARY ---\n", summary)

    asyncio.run(test())