# verify_refactor.py
import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

# Load env
load_dotenv()

# Mock settings if needed, but we rely on .env
from app.config import settings

async def test_pipeline():
    logger.info("🧪 Testing Refactored Pipeline...")
    
    from core.pipeline import run_pipeline
    
    query = "AI trends in 2025"
    logger.info(f"Running query: {query}")
    
    try:
        result = await run_pipeline(query)
        
        if result["status"] == "success":
            logger.success("✅ Pipeline run successful!")
            logger.info(f"Intent: {result.get('intent')}")
            logger.info(f"Summary: {result.get('summary')[:100]}...")
            logger.info(f"Report Length: {len(result.get('final_report', ''))}")
        else:
            logger.error(f"❌ Pipeline failed: {result.get('message')}")
            
    except Exception as e:
        logger.exception(f"❌ Exception during pipeline run: {e}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
