# core/summarizer.py
"""
Summarizer Module
-----------------
Provides functionality to summarize text chunks using the LLM.
Uses the unified core.llm module for robust API calls.
"""

from typing import List

from loguru import logger

from core.llm import llm_generate
from core.types import Document


class Summarizer:
    """
    Summarizes text contexts into concise insights.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model

    async def summarize(self, query: str, contexts: List[str]) -> str:
        """
        Summarizes a list of text contexts relevant to a query.
        
        Args:
            query (str): The user's query.
            contexts (List[str]): List of text chunks.
            
        Returns:
            str: A concise summary.
        """
        if not contexts:
            return "No context found to summarize."

        # Limit context to avoid context window issues (though Gemini has large window)
        context_text = "\n\n".join(contexts[:10])
        logger.info(f"🧠 [SUMMARIZER] Summarizing {len(contexts)} chunks for query: {query}")

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
            return await llm_generate(prompt, model=self.model)
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return "Failed to summarize context."


async def summarize_docs(docs: List[Document]) -> str:
    """
    Summarizes a list of Document objects.
    
    Args:
        docs (List[Document]): List of documents.
        
    Returns:
        str: Bullet-point summary.
    """
    if not docs:
        return ""

    text = "\n\n".join(d.page_content[:2000] for d in docs)

    prompt = f"""
    You are a concise research summarizer.

    Summarize the following content into clear bullet points:

    CONTENT:
    {text}
    """

    try:
        return await llm_generate(prompt, model="gemini-2.0-flash")
    except Exception as e:
        logger.error(f"❌ Document summarization failed: {e}")
        return ""