# core/rag_manager.py
"""
Neon + pgvector RAG Manager.

- Chunks documents
- Embeds with Gemini (text-embedding-004)
- Stores chunks & embeddings in Neon (document_chunks table)
- Performs vector similarity search with pgvector
"""

import json
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy import text

from core.llm import embed_texts
from core.types import Document
from infra.db import db_execute, db_query


def _chunk_text(text: str, chunk_size: int = 1500, overlap: int = 150) -> List[str]:
    """Simple character-based splitter."""
    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap

    return chunks


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure metadata is JSON-serializable and flat-ish."""
    clean: Dict[str, Any] = {}
    for k, v in (metadata or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = ", ".join(map(str, v))
        elif isinstance(v, dict):
            clean[k] = json.dumps(v, ensure_ascii=False)
            # Alternatively: store nested dict as JSON string
        else:
            clean[k] = str(v)
    return clean


class VectorStoreManager:
    """
    VectorStoreManager for Neon + pgvector.

    API:
        await clear_store()
        await add_documents(documents)
        await search(query, k=5)
    """

    async def clear_store(self) -> None:
        logger.warning("🧹 Clearing document_chunks table...")
        sql = "TRUNCATE document_chunks RESTART IDENTITY;"
        await db_execute(sql)
        logger.info("✅ Vector store cleared.")

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        documents: list of dicts with keys:
            - page_content: str
            - metadata: dict
        """
        if not documents:
            logger.warning("No documents provided to add to vector store.")
            return

        logger.info(f"📄 Received {len(documents)} documents. Chunking & embedding...")

        # 1) Build chunks
        chunks: List[Dict[str, Any]] = []
        for doc in documents:
            text = doc.get("page_content") or ""
            meta = _sanitize_metadata(doc.get("metadata", {}))
            for chunk in _chunk_text(text):
                chunks.append({"content": chunk, "metadata": meta})

        logger.info(f"✂️ Split into {len(chunks)} chunks.")

        if not chunks:
            logger.warning("No chunks produced from documents.")
            return

        # 2) Embed in batches
        BATCH_SIZE = 16
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            texts = [c["content"] for c in batch]

            try:
                embeddings = await embed_texts(texts)
            except Exception as e:
                logger.error(f"Embedding batch {i} failed: {e}")
                continue

            # 3) Insert into Neon
            sql = """
            INSERT INTO document_chunks (content, metadata, embedding)
            VALUES (%s, %s, %s)
            """

            params_list = [
                (c["content"], json.dumps(c["metadata"]), emb)
                for c, emb in zip(batch, embeddings)
            ]

            for params in params_list:
                await db_execute(sql, list(params))

            logger.info(f"  > Stored chunks {i+1}–{i+len(batch)}/{len(chunks)}")

        logger.info("✅ All chunks stored in Neon.")

    async def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Vector similarity search using pgvector <-> operator.
        Returns a list of core.types.Document.
        """
        logger.info(f"🔍 Vector search for: {query!r}")

        [query_emb] = await embed_texts([query])

        sql = text(
            """
            SELECT content, metadata, embedding <-> :q AS distance
            FROM document_chunks
            ORDER BY embedding <-> :q
            LIMIT :k
            """
        )

        rows = await db_query(sql.text, {"q": query_emb, "k": k})

        docs: List[Document] = []
        for content, metadata, distance in rows:
            try:
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            except Exception:
                meta = {}
            m = dict(meta or {})
            m["score"] = float(distance)
            docs.append(Document(page_content=content, metadata=m))

        logger.info(f"✅ Retrieved {len(docs)} chunks from vector store.")
        return docs
