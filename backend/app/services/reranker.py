"""Cross-encoder re-ranking of retrieved chunks."""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.services.document_processor import ChunkRecord
from app.utils.retry import with_retry

logger = logging.getLogger(__name__)


@lru_cache
def get_reranker() -> CrossEncoder:
    settings = get_settings()
    logger.info("Loading cross-encoder: %s", settings.reranker_model)
    return CrossEncoder(settings.reranker_model)


@with_retry(attempts=2)
def rerank(
    question: str,
    candidates: list[tuple[ChunkRecord, float]],
    top_n: int | None = None,
) -> list[tuple[ChunkRecord, float]]:
    """
    Re-score FAISS candidates with a cross-encoder.

    Returns chunks sorted by cross-encoder score (descending), truncated to top_n.
    Logs pre- and post-rerank order for README / debugging screenshots.
    """
    settings = get_settings()
    top_n = top_n or settings.rerank_top_n
    if not candidates:
        return []

    logger.info("=== PRE-RERANK (FAISS order) ===")
    for i, (chunk, score) in enumerate(candidates, start=1):
        logger.info(
            "  #%s id=%s page=%s faiss=%.4f preview=%r",
            i,
            chunk.id,
            chunk.page,
            score,
            chunk.text[:80],
        )

    model = get_reranker()
    pairs = [(question, c.text) for c, _ in candidates]
    ce_scores = model.predict(pairs)

    rescored = [
        (chunk, float(ce_score))
        for (chunk, _), ce_score in zip(candidates, ce_scores, strict=False)
    ]
    rescored.sort(key=lambda x: x[1], reverse=True)
    top = rescored[:top_n]

    logger.info("=== POST-RERANK (cross-encoder order) ===")
    for i, (chunk, score) in enumerate(top, start=1):
        logger.info(
            "  #%s id=%s page=%s ce=%.4f preview=%r",
            i,
            chunk.id,
            chunk.page,
            score,
            chunk.text[:80],
        )

    return top
