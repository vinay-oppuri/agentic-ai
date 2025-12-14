# app/main.py
"""
Main Application
----------------
FastAPI entry point. Configures middleware, routes, and startup events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.routes.pipeline import router as pipeline_router
from app.routes.chat import router as chat_router
from infra.db import init_schema


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(title=settings.app_name)

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(pipeline_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")

    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.
    Initializes database schema (if DB is reachable).
    """
    logger.info("🚀 Starting Agentic AI Backend...")
    try:
        await init_schema()
    except Exception as e:
        logger.warning(f"⚠️ Database initialization skipped/failed: {e}")


@app.get("/")
def home():
    """Health check endpoint."""
    return {"message": "Agentic Research Backend Running 🚀"}
