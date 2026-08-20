"""POST /api/upload — ingest a single PDF into FAISS."""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models import UploadResponse
from app.services.document_processor import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings = get_settings()
    document_id = str(uuid.uuid4())
    dest = settings.upload_dir / f"{document_id}_{Path(file.filename).name}"

    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        result = await asyncio.to_thread(ingest_pdf, dest, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return UploadResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        num_pages=result["num_pages"],
        num_chunks=result["num_chunks"],
    )
