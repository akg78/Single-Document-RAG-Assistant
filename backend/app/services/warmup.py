"""Preload local ML models to avoid cold-start latency on first upload/query."""

from __future__ import annotations

import logging
import time

from app.config import get_settings

logger = logging.getLogger(__name__)


def warmup_models(*, include_reranker: bool = False) -> None:
    """
    Load embedding model (and optionally reranker) into memory.

    Runs during app startup when PRELOAD_MODELS=true so POST /api/upload
    skips the ~8–10s HuggingFace load on the first request.
    """
    settings = get_settings()
    if not settings.preload_models:
        logger.info("Model preload disabled (PRELOAD_MODELS=false)")
        return

    from app.services.embeddings import embed_query, get_embedding_model

    t0 = time.perf_counter()
    get_embedding_model()
    embed_query("warmup")  # one forward pass to fully load weights
    logger.info("Embedding model ready in %.1fs", time.perf_counter() - t0)

    if include_reranker:
        from app.services.reranker import get_reranker

        t1 = time.perf_counter()
        get_reranker()
        logger.info("Reranker ready in %.1fs", time.perf_counter() - t1)
