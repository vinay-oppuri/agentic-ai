# core/rag_manager.py
"""
RAG Manager Module
------------------
Manages the retrieval-augmented generation pipeline.
- Chunks documents.
- Generates embeddings.
- Stores chunks in Neon (PostgreSQL) with pgvector.
- Performs semantic search.
"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from core.llm import embed_texts
from core.types import Document
from infra.db import db_execute, db_query
from app.config import settings


def _chunk_text(text: str, chunk_size: int = 1500, overlap: int = 150) -> List[str]:
    """
    Splits text into overlapping chunks.
    
    Args:
        text (str): Input text.
        chunk_size (int): Max characters per chunk.
        overlap (int): Overlap characters.
        
    Returns:
        List[str]: List of text chunks.
    """
    chunks = []
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
    """
    Ensures metadata values are JSON-serializable.
    """
    clean = {}
    for k, v in (metadata or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = ", ".join(map(str, v))
        elif isinstance(v, dict):
            clean[k] = json.dumps(v, ensure_ascii=False)
        else:
            clean[k] = str(v)
    return clean


class VectorStoreManager:
    """
    Manages vector storage and retrieval using Neon + pgvector.
    """

    async def clear_store(self) -> None:
        """Truncates the document_chunks table."""
        logger.warning("🧹 Clearing vector store...")
        await db_execute("TRUNCATE document_chunks RESTART IDENTITY;")
        logger.info("✅ Vector store cleared.")

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Chunks, embeds, and stores documents.
        
        Args:
            documents (List[Dict]): List of dicts with 'page_content' and 'metadata'.
        """
        if not documents:
            return

        logger.info(f"📄 Processing {len(documents)} documents...")

        # 1. Chunking
        chunks: List[Dict[str, Any]] = []
        for doc in documents:
            text = doc.get("page_content") or ""
            meta = _sanitize_metadata(doc.get("metadata", {}))
            for chunk_text in _chunk_text(text):
                chunks.append({"content": chunk_text, "metadata": meta})

        if not chunks:
            return

        logger.info(f"✂️ Created {len(chunks)} chunks.")

        # 2. Embedding & Storage (Batched)
        BATCH_SIZE = 16
        sql = """
        INSERT INTO document_chunks (content, metadata, embedding)
        VALUES (%s, %s, %s)
        """

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            texts = [c["content"] for c in batch]

            try:
                embeddings = await embed_texts(texts, api_key=settings.google_key_rag)
            except Exception as e:
                logger.error(f"❌ Embedding batch {i} failed: {e}")
                continue

            # Insert batch
            for c, emb in zip(batch, embeddings):
                if not emb: 
                    continue # Skip failed embeddings
                
                await db_execute(sql, [c["content"], json.dumps(c["metadata"]), emb])

            logger.info(f"  > Stored chunks {i+1}-{min(i+len(batch), len(chunks))}")

        logger.info("✅ All chunks stored.")

    async def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Performs semantic search.
        
        Args:
            query (str): The search query.
            k (int): Number of results to return.
            
        Returns:
            List[Document]: Top k matching documents.
        """
        logger.info(f"🔍 Searching for: {query}")

        # Generate query embedding
        embeddings = await embed_texts([query], api_key=settings.google_key_rag)
        if not embeddings or not embeddings[0]:
            logger.warning("⚠️ Failed to embed query.")
            return []
            
        query_emb = embeddings[0]

        # SQL for cosine similarity (using <-> operator for L2 distance, order by distance ASC)
        # Note: For cosine similarity with normalized vectors, L2 distance order is same as cosine distance.
        # pgvector's <-> is L2 distance. <=> is cosine distance. 
        # text-embedding-004 vectors are normalized, so either works, but <=> is explicit for cosine.
        # Let's use <=> for cosine distance.
        
        sql = """
        SELECT content, metadata, embedding <=> %s::vector AS distance
        FROM document_chunks
        ORDER BY distance ASC
        LIMIT %s
        """

        rows = await db_query(sql, [query_emb, k])

        docs = []
        for content, metadata, distance in rows:
            try:
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
            except Exception:
                meta = {}
            
            # Convert distance to similarity score (approximate)
            # Cosine distance = 1 - cosine_similarity
            # So similarity = 1 - distance
            meta["score"] = 1.0 - float(distance)
            
            docs.append(Document(page_content=content, metadata=meta))

        logger.info(f"✅ Retrieved {len(docs)} relevant chunks.")
        return docs
