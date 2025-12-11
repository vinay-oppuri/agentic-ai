# infra/db.py
from loguru import logger
from psycopg import AsyncConnection
from psycopg.rows import tuple_row
from app.config import settings
import json
import asyncio

DATABASE_URL = settings.database_url

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL missing from .env")


# ----------------------------------------------------
# Connection helper
# ----------------------------------------------------
async def get_conn():
    """
    Opens a new async connection to Neon.
    We do NOT use pooling because Neon idle timeout
    can break long-lived pooled connections.
    """
    try:
        conn = await AsyncConnection.connect(
            DATABASE_URL,
            autocommit=True
        )
        return conn
    except Exception as e:
        logger.error(f"❌ DB connection failed: {e}")
        raise e


# ----------------------------------------------------
# Initialize schema (AUTO-MIGRATION)
# ----------------------------------------------------
async def init_schema():
    """
    Ensures that required tables & columns exist.
    Handles pgvector and missing 'embedding' column.
    """

    # enable pgvector extension
    enable_vector = """
    CREATE EXTENSION IF NOT EXISTS vector;
    """

    # create table if missing
    create_table = """
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        doc_id TEXT,
        content TEXT,
        metadata JSONB,
        embedding vector(3072),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """

    # add missing embedding column (if table exists but older schema)
    add_embedding_column = """
    ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS embedding vector(3072);
    """

    create_pipeline_results = """
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
            await cur.execute(create_table)
            await cur.execute(add_embedding_column)
            await cur.execute(create_pipeline_results)

        await conn.close()
        logger.info("🛠️ Database schema initialized + auto-migrated.")

    except Exception as e:
        logger.error(f"❌ Schema init failed: {e}")
        raise e


# ----------------------------------------------------
# Execute query (INSERT / UPDATE / DELETE)
# ----------------------------------------------------
async def db_execute(sql: str, params=None):
    params = params or []

    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
        await conn.close()

    except Exception as e:
        logger.error(f"❌ DB execute error: {e}")
        raise e


# ----------------------------------------------------
# Query rows (SELECT)
# ----------------------------------------------------
async def db_query(sql: str, params=None):
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
        raise e


# ----------------------------------------------------
# Save full pipeline result
# ----------------------------------------------------
async def save_pipeline_result(idea: str, intent: dict, strategy: dict, report_md: str):
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


# ----------------------------------------------------
# Optional manual test
# ----------------------------------------------------
async def test_connection():
    try:
        rows = await db_query("SELECT 1;")
        logger.info(f"✅ Neon connection OK: {rows}")
        return rows
    except Exception as e:
        logger.error(f"❌ Neon test failed: {e}")
        raise e