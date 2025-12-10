# infra/db.py
from loguru import logger
from psycopg import AsyncConnection
from psycopg.rows import tuple_row
from app.config import settings
import json

DATABASE_URL = settings.database_url

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL missing from .env")


# -----------------------------
# Create a fresh connection each time
# -----------------------------
async def get_conn():
    """
    Opens a new async connection to Neon.
    Pooling is disabled to avoid SSL/channel binding issues.
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


# -----------------------------
# Execute (INSERT / UPDATE / DELETE)
# -----------------------------
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


# -----------------------------
# Query (SELECT)
# -----------------------------
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


# -----------------------------
# Save pipeline results
# -----------------------------
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

    rows = await db_query(sql, params)
    return rows[0][0] if rows else None


# -----------------------------
# Optional: test connection
# -----------------------------
async def test_connection():
    try:
        rows = await db_query("SELECT 1;")
        logger.info(f"✅ Neon connection OK: {rows}")
        return rows
    except Exception as e:
        logger.error(f"❌ Neon test failed: {e}")
        raise e