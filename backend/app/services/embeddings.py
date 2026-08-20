"""Local sentence-transformers embeddings with retry."""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import get_settings
from app.utils.retry import with_retry

logger = logging.getLogger(__name__)


@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    settings = get_settings()
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 64},
    )


@with_retry(attempts=3)
def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)


@with_retry(attempts=3)
def embed_query(text: str) -> list[float]:
    model = get_embedding_model()
    return model.embed_query(text)


def to_numpy(vectors: list[list[float]]) -> np.ndarray:
    return np.asarray(vectors, dtype=np.float32)
