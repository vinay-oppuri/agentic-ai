# core/retreiver_selector.py
"""
retreiver_selector.py (typo preserved to match existing filename)
-----------------------------------------------------------------
Hybrid retriever:
 - Dense semantic search using Neon + pgvector (VectorStoreManager)
 - Optional sparse BM25 search (in-memory)
"""

from typing import List

from loguru import logger

from core.rag_manager import VectorStoreManager
from core.types import Document

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not installed → sparse BM25 retriever disabled.")


class RetrieverSelector:
    def __init__(self):
        logger.info("Initializing RetrieverSelector (dense + optional sparse)...")
        self.vector_manager = VectorStoreManager()

        self.bm25 = None
        self.bm25_docs: List[Document] = []

    async def _build_sparse_index(self):
        """
        Load all docs from Neon (via vector manager search many times or separate table)
        and build BM25 index.
        In this initial version, we skip full corpus and rely on dense only if BM25 is unavailable.
        """
        # NOTE: To keep this simple & fast for now, we skip preloading entire corpus.
        # You can extend this to load all document_chunks and index them.
        logger.info("BM25 sparse index not implemented (using dense-only for now).")

    async def retrieve(self, query: str, k: int = 6) -> List[Document]:
        """
        Hybrid retrieval: currently dense-only via vector store.
        Extend later to mix BM25 if desired.
        """
        logger.info(f"🔍 Retrieving for query: {query!r}")

        # Dense semantic retrieval from Neon vector store
        dense_docs = await self.vector_manager.search(query, k=k)

        # If BM25 is wired, you could merge here, but for now:
        logger.info(f"✅ Retrieved {len(dense_docs)} dense chunks (no sparse merge).")
        return dense_docs


# Debug usage
if __name__ == "__main__":
    import asyncio

    async def _test():
        sel = RetrieverSelector()
        q = (
            "What are competitors for a GitHub repository analysis tool for developers "
            "that finds bugs, vulnerabilities, and code quality issues?"
        )
        docs = await sel.retrieve(q, k=5)
        print("\n=== Retrieved ===\n")
        for d in docs:
            print("-", d.page_content[:150], "...\n")

    asyncio.run(_test())
