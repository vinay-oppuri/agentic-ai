
import asyncio
import os
from app.config import settings
from psycopg import AsyncConnection

async def test_conn():
    print(f"DEBUG: DATABASE_URL from settings: {settings.database_url[:15]}... (len={len(settings.database_url)})")
    
    try:
        print("DEBUG: Attempting to connect...")
        conn = await AsyncConnection.connect(settings.database_url, autocommit=True)
        print("DEBUG: Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"DEBUG: Connection failed!")
        print(f"DEBUG: Exception type: {type(e)}")
        print(f"DEBUG: Exception repr: {repr(e)}")
        print(f"DEBUG: Exception str: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_conn())
