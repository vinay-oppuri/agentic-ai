# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.pipeline import router as pipeline_router
from app.routes.chat import router as chat_router  # if you still use it


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(pipeline_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")  # optional

    return app


app = create_app()


@app.get("/")
def home():
    return {"message": "Agentic Research Backend Running 🚀"}
