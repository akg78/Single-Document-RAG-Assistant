"""FastAPI entrypoint: CORS + routers + startup index restore."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, reload_settings
from app.models import HealthResponse
from app.routes import evaluate, query, suggestions, topics, tts, upload
from app.services.document_processor import try_restore_latest
from app.services.warmup import warmup_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try_restore_latest()
    warmup_models()
    yield


def create_app() -> FastAPI:
    reload_settings()
    settings = get_settings()

    application = FastAPI(
        title="Single-Document RAG Assistant",
        description="PDF upload → FAISS → cross-encoder rerank → LCEL generation → RAGAS logging",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(upload.router)
    application.include_router(query.router)
    application.include_router(suggestions.router)
    application.include_router(topics.router)
    application.include_router(tts.router)
    application.include_router(evaluate.router)

    @application.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return application


app = create_app()
