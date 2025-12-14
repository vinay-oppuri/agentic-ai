# infra/db.py
"""
Database Infrastructure Module
------------------------------
Handles asynchronous connections to the Neon (PostgreSQL) database.
Includes automatic schema initialization, migration, and helper functions
for executing queries.

Key Features:
- Async connection management with timeouts.
- Automatic schema migration (pgvector support).
- Robust error handling (logs errors instead of crashing on optional ops).
"""

import json
import asyncio
from typing import Any, List, Optional, Tuple

from loguru import logger
from psycopg import AsyncConnection
from psycopg.rows import tuple_row
from app.config import settings

# Constants
DATABASE_URL = settings.database_url
CONNECT_TIMEOUT = 3.0  # seconds
EMBEDDING_DIM = 768    # text-embedding-004 dimension


async def get_conn() -> AsyncConnection:
    """
    Establishes a new asynchronous connection to the database.
    
    Returns:
        AsyncConnection: A new psycopg connection object.
        
    Raises:
        RuntimeError: If DATABASE_URL is not set.
        Exception: If connection fails or times out.
    """
    if not DATABASE_URL:
        raise RuntimeError("❌ DATABASE_URL missing from .env")

    try:
        # We do not use pooling here because Neon's idle timeout 
        # can break long-lived pooled connections.
        conn = await asyncio.wait_for(
            AsyncConnection.connect(DATABASE_URL, autocommit=True),
            timeout=CONNECT_TIMEOUT
        )
        return conn
    except Exception as e:
        logger.error(f"❌ DB connection failed: {repr(e)}")
        raise e


async def is_db_available() -> bool:
    """
    Checks if the database is currently reachable.
    
    Returns:
        bool: True if connection succeeds, False otherwise.
    """
    try:
        conn = await get_conn()
        await conn.close()
        return True
    except Exception:
        return False


async def init_schema() -> None:
    """
    Initializes the database schema.
    
    - Enables `vector` extension.
    - Creates `document_chunks` and `pipeline_results` tables.
    - Migrates existing columns to the correct embedding dimension.
    
    Note:
        Failures here are logged but do not raise exceptions, allowing
        the application to start in a degraded state (without persistence).
    """
    # SQL Statements
    enable_vector = "CREATE EXTENSION IF NOT EXISTS vector;"
    
    create_chunks_table = f"""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        doc_id TEXT,
        content TEXT,
        metadata JSONB,
        embedding vector({EMBEDDING_DIM}),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # Ensure embedding column exists
    add_embedding_col = f"""
    ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIM});
    """
    
    # Migration: Force correct dimension
    alter_embedding_col = f"""
    ALTER TABLE document_chunks
    ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM});
    """

    create_results_table = """
    CREATE TABLE IF NOT EXISTS pipeline_results (
        id SERIAL PRIMARY KEY,
        idea TEXT,
        intent_json JSONB,
        strategy_json JSONB,
        report_md TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """

    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute(enable_vector)
            await cur.execute(create_chunks_table)
            await cur.execute(add_embedding_col)
            
            # Attempt migration (might fail if data is incompatible, so we catch it)
            try:
                await cur.execute(alter_embedding_col)
            except Exception as e:
                logger.warning(f"⚠️ Could not alter embedding column: {e}")

            await cur.execute(create_results_table)

        await conn.close()
        logger.info("🛠️ Database schema initialized + auto-migrated.")

    except Exception as e:
        logger.error(f"❌ Schema init failed: {repr(e)}")


async def db_execute(sql: str, params: Optional[List[Any]] = None) -> None:
    """
    Executes a DML statement (INSERT, UPDATE, DELETE).
    
    Args:
        sql (str): The SQL query.
        params (list, optional): Query parameters.
    """
    params = params or []
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
        await conn.close()
    except Exception as e:
        logger.error(f"❌ DB execute error: {e}")
        # raise e  <-- Suppressed for graceful degradation

async def db_query(sql: str, params: Optional[List[Any]] = None) -> List[Tuple]:
    """
    Executes a SELECT statement and returns rows.
    
    Args:
        sql (str): The SQL query.
        params (list, optional): Query parameters.
        
    Returns:
        List[Tuple]: A list of rows (tuples).
    """
    params = params or []
    try:
        conn = await get_conn()
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
        await conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ DB query error: {e}")
        return [] # Return empty list on failure


async def save_pipeline_result(idea: str, intent: dict, strategy: dict, report_md: str) -> Optional[int]:
    """
    Saves the full result of a pipeline run.
    
    Args:
        idea (str): The initial user query/idea.
        intent (dict): Parsed intent data.
        strategy (dict): Execution strategy/plan.
        report_md (str): Final generated report.
        
    Returns:
        int: The ID of the inserted record, or None if failed.
    """
    sql = """
    INSERT INTO pipeline_results (idea, intent_json, strategy_json, report_md)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    
    params = [
        idea,
        json.dumps(intent, ensure_ascii=False),
        json.dumps(strategy, ensure_ascii=False),
        report_md,
    ]

    try:
        rows = await db_query(sql, params)
        return rows[0][0] if rows else None
    except Exception as e:
        logger.error(f"❌ Failed to save pipeline result: {e}")
        raise e