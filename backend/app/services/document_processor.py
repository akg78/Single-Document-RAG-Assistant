"""PDF loading, chunking, FAISS indexing, and persistence."""

from __future__ import annotations

import json
import logging
import pickle
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import get_settings
from app.services.embeddings import embed_query, embed_texts, get_embedding_model, to_numpy

logger = logging.getLogger(__name__)

NO_DOCUMENT_MSG = "No document indexed. Upload a PDF first."


@dataclass
class ChunkRecord:
    id: str
    text: str
    source: str
    page: int
    chunk_index: int
    document_id: str


class DocumentStore:
    """In-memory + on-disk FAISS store for a single active document."""

    def __init__(self) -> None:
        self.document_id: str | None = None
        self.filename: str | None = None
        self.num_pages: int = 0
        self.chunks: list[ChunkRecord] = []
        self.index: faiss.Index | None = None

    @property
    def indexed(self) -> bool:
        return self.index is not None and len(self.chunks) > 0


# Process-wide singleton (single-document RAG)
store = DocumentStore()


def _activate_store(
    document_id: str,
    chunks: list[ChunkRecord],
    index: faiss.Index,
    *,
    filename: str | None = None,
    num_pages: int | None = None,
) -> None:
    store.document_id = document_id
    store.filename = filename
    store.chunks = chunks
    store.index = index
    store.num_pages = num_pages if num_pages is not None else len({c.page for c in chunks})


def _splitter() -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def load_and_chunk_pdf(pdf_path: Path, document_id: str) -> list[ChunkRecord]:
    """Extract text per page and chunk with page metadata preserved."""
    reader = PdfReader(str(pdf_path))
    splitter = _splitter()

    chunks: list[ChunkRecord] = []
    chunk_index = 0
    filename = pdf_path.name

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1  # 1-indexed for UI citations
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            continue

        for piece in splitter.split_text(page_text):
            piece = piece.strip()
            if not piece:
                continue
            record = ChunkRecord(
                id=f"{document_id}-{chunk_index}",
                text=piece,
                source=filename,
                page=page_num,
                chunk_index=chunk_index,
                document_id=document_id,
            )
            chunks.append(record)
            logger.debug(
                "chunk[%s] page=%s chars=%s preview=%r",
                chunk_index,
                page_num,
                len(piece),
                piece[:120],
            )
            chunk_index += 1

    return chunks

def build_faiss_index(chunks: list[ChunkRecord]) -> faiss.IndexFlatIP:
    """Build IndexFlatIP over unit-normalized embeddings (cosine similarity)."""
    texts = [c.text for c in chunks]
    vectors = to_numpy(embed_texts(texts))
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    return index


def persist_index(document_id: str, chunks: list[ChunkRecord], index: faiss.Index) -> None:
    settings = get_settings()
    dest = settings.faiss_dir / document_id
    dest.mkdir(parents=True, exist_ok=True)
    index_path = dest / "index.faiss"
    chunks_path = dest / "chunks.pkl"
    meta_path = dest / "meta.json"

    def _write_chunks() -> None:
        with chunks_path.open("wb") as f:
            pickle.dump([asdict(c) for c in chunks], f, protocol=pickle.HIGHEST_PROTOCOL)

    def _write_meta() -> None:
        meta = {
            "document_id": document_id,
            "filename": chunks[0].source if chunks else None,
            "num_chunks": len(chunks),
        }
        meta_path.write_text(json.dumps(meta, separators=(",", ":")), encoding="utf-8")

    with ThreadPoolExecutor(max_workers=3) as pool:
        faiss_future = pool.submit(faiss.write_index, index, str(index_path))
        chunks_future = pool.submit(_write_chunks)
        meta_future = pool.submit(_write_meta)
        faiss_future.result()
        chunks_future.result()
        meta_future.result()


def load_persisted(document_id: str) -> tuple[list[ChunkRecord], faiss.Index, dict[str, Any]]:
    settings = get_settings()
    dest = settings.faiss_dir / document_id
    index = faiss.read_index(str(dest / "index.faiss"))
    with open(dest / "chunks.pkl", "rb") as f:
        raw = pickle.load(f)
    chunks = [ChunkRecord(**c) for c in raw]
    meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
    return chunks, index, meta


def ingest_pdf(pdf_path: Path, document_id: str | None = None) -> dict[str, Any]:
    """Full ingestion: load → chunk → embed → FAISS → persist → activate store."""
    document_id = document_id or str(uuid.uuid4())

    # Overlap PDF parsing with model load when the model is not yet cached
    with ThreadPoolExecutor(max_workers=2) as pool:
        chunks_future = pool.submit(load_and_chunk_pdf, pdf_path, document_id)
        model_future = pool.submit(get_embedding_model)
        model_future.result()
        chunks = chunks_future.result()

    if not chunks:
        raise ValueError("No text could be extracted from the PDF.")

    num_pages = len({c.page for c in chunks})
    index = build_faiss_index(chunks)
    persist_index(document_id, chunks, index)
    _activate_store(document_id, chunks, index, filename=pdf_path.name, num_pages=num_pages)

    logger.info(
        "Indexed document_id=%s filename=%s pages=%s chunks=%s",
        document_id,
        pdf_path.name,
        num_pages,
        len(chunks),
    )
    return {
        "document_id": document_id,
        "filename": pdf_path.name,
        "num_pages": num_pages,
        "num_chunks": len(chunks),
    }


def query_index(
    question: str,
    k: int | None = None,
    document_id: str | None = None,
) -> list[tuple[ChunkRecord, float]]:
    """Return top-k chunks with similarity scores (identical for identical queries)."""
    settings = get_settings()
    k = k or settings.faiss_top_k

    if document_id and (not store.indexed or store.document_id != document_id):
        chunks, index, meta = load_persisted(document_id)
        _activate_store(document_id, chunks, index, filename=meta.get("filename"))

    if not store.indexed or store.index is None:
        raise RuntimeError(NO_DOCUMENT_MSG)

    q = to_numpy([embed_query(question)])
    k = min(k, len(store.chunks))
    scores, indices = store.index.search(q, k)

    results: list[tuple[ChunkRecord, float]] = []
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0:
            continue
        results.append((store.chunks[int(idx)], float(score)))
    return results


def try_restore_latest() -> bool:
    """On startup, restore the most recently modified FAISS folder if present."""
    settings = get_settings()
    dirs = [p for p in settings.faiss_dir.iterdir() if p.is_dir()]
    if not dirs:
        return False
    latest = max(dirs, key=lambda p: p.stat().st_mtime)
    try:
        chunks, index, meta = load_persisted(latest.name)
        _activate_store(latest.name, chunks, index, filename=meta.get("filename"))
        logger.info("Restored FAISS index for document_id=%s", latest.name)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to restore index: %s", exc)
        return False
