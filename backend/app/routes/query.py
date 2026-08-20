"""POST /api/query — RAG question answering."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models import DocumentStatus, QueryRequest, QueryResponse
from app.services.document_processor import store
from app.services.rag_pipeline import run_rag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_document(body: QueryRequest) -> QueryResponse:
    try:
        return run_rag(
            question=body.question.strip(),
            document_id=body.document_id,
            top_k=body.top_k,
            run_eval=True,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc


@router.get("/document", response_model=DocumentStatus)
async def document_status() -> DocumentStatus:
    return DocumentStatus(
        document_id=store.document_id,
        filename=store.filename,
        num_chunks=len(store.chunks),
        indexed=store.indexed,
        meta={"num_pages": store.num_pages},
    )
