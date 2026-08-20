"""LCEL RAG pipeline: route → retrieve → rerank → generate → evaluate."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.models import QueryRouteInfo, QueryResponse, RagasScores, RerankComparison, SourceChunk
from app.services.document_processor import NO_DOCUMENT_MSG, ChunkRecord, query_index, store
from app.services.evaluator import compute_ragas_scores, log_evaluation
from app.services.reranker import rerank

logger = logging.getLogger(__name__)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a careful document assistant. Answer ONLY using the provided context. "
                "If the answer is not in the context, say exactly: "
                "'The answer is not in this document.' "
                "Do not invent facts. When you use information, mention the page number(s) "
                "like (p. N). Keep answers concise and grounded."
            ),
        ),
        (
            "human",
            "Context:\n{context}\n\nQuestion: {question}\n\nGrounded answer:",
        ),
    ]
)

ROUTE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Classify the user question about a single document.\n"
                "Return ONLY valid JSON with keys:\n"
                '  "query_type": one of "single_fact", "multi_part", "summarization",\n'
                '  "sub_questions": array of strings (1 item for single_fact/summarization; '
                "2+ for multi_part).\n"
                "For multi-part questions (e.g. 'What is X and how does it compare to Y?'), "
                "decompose into clear sub-questions."
            ),
        ),
        ("human", "{question}"),
    ]
)


def _get_llm(temperature: float = 0.0) -> ChatOpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to backend/.env to enable LLM generation."
        )
    kwargs: dict[str, Any] = {
        "model": settings.openai_model,
        "api_key": settings.openai_api_key,
        "temperature": temperature,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def _parse_route(raw: str, question: str) -> QueryRouteInfo:
    try:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        data = json.loads(match.group(0) if match else raw)
        qtype = data.get("query_type", "single_fact")
        if qtype not in {"single_fact", "multi_part", "summarization"}:
            qtype = "single_fact"
        subs = data.get("sub_questions") or [question]
        if not isinstance(subs, list) or not subs:
            subs = [question]
        return QueryRouteInfo(query_type=qtype, sub_questions=[str(s) for s in subs])
    except Exception:  # noqa: BLE001
        # Heuristic fallback without LLM
        if any(w in question.lower() for w in ("summarize", "summary", "overview", "key points")):
            return QueryRouteInfo(query_type="summarization", sub_questions=[question])
        if " and " in question.lower() or "?" in question.strip()[:-1]:
            parts = re.split(r"\band\b|\?", question, flags=re.IGNORECASE)
            parts = [p.strip(" .") for p in parts if len(p.strip(" .")) > 8]
            if len(parts) >= 2:
                return QueryRouteInfo(query_type="multi_part", sub_questions=parts[:4])
        return QueryRouteInfo(query_type="single_fact", sub_questions=[question])


def route_query(question: str) -> QueryRouteInfo:
    settings = get_settings()
    if not settings.openai_api_key:
        return _parse_route("", question)
    try:
        chain = ROUTE_PROMPT | _get_llm(temperature=0) | StrOutputParser()
        raw = chain.invoke({"question": question})
        return _parse_route(raw, question)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Routing LLM failed, heuristic used: %s", exc)
        return _parse_route("", question)


def _format_context(chunks: list[tuple[ChunkRecord, float]]) -> str:
    blocks: list[str] = []
    for i, (chunk, score) in enumerate(chunks, start=1):
        blocks.append(
            f"[Source {i} | id={chunk.id} | page={chunk.page} | score={score:.4f}]\n{chunk.text}"
        )
    return "\n\n---\n\n".join(blocks)


def _to_source_chunks(
    items: list[tuple[ChunkRecord, float]],
    snippet_len: int = 280,
) -> list[SourceChunk]:
    out: list[SourceChunk] = []
    for chunk, score in items:
        snippet = chunk.text if len(chunk.text) <= snippet_len else chunk.text[:snippet_len] + "…"
        out.append(
            SourceChunk(
                id=chunk.id,
                page=chunk.page,
                chunk_index=chunk.chunk_index,
                snippet=snippet,
                score=round(score, 4),
                source=chunk.source,
            )
        )
    return out


def retrieve_and_rerank(
    question: str,
    route: QueryRouteInfo,
    top_k: int | None = None,
) -> tuple[list[tuple[ChunkRecord, float]], list[tuple[ChunkRecord, float]]]:
    """
    Retrieve for each sub-question, merge unique chunks, then cross-encoder rerank.
    Returns (pre_rerank_merged, post_rerank).
    """
    settings = get_settings()
    k = top_k or settings.faiss_top_k
    merged: dict[str, tuple[ChunkRecord, float]] = {}

    queries = route.sub_questions or [question]
    for sq in queries:
        hits = query_index(sq, k=k)
        for chunk, score in hits:
            prev = merged.get(chunk.id)
            if prev is None or score > prev[1]:
                merged[chunk.id] = (chunk, score)

    pre = sorted(merged.values(), key=lambda x: x[1], reverse=True)[:k]
    post = rerank(question, pre, top_n=settings.rerank_top_n)
    return pre, post


def generate_answer(question: str, ranked: list[tuple[ChunkRecord, float]]) -> str:
    settings = get_settings()
    context = _format_context(ranked)

    if not settings.openai_api_key:
        # Deterministic offline demo answer so the UI still works without a key
        if not ranked:
            return "The answer is not in this document."
        top = ranked[0][0]
        return (
            f"(Offline mode — set OPENAI_API_KEY for full generation.) "
            f"Most relevant passage is on page {top.page}: {top.text[:400]}"
        )

    chain = ANSWER_PROMPT | _get_llm(temperature=0) | StrOutputParser()
    return chain.invoke({"context": context, "question": question}).strip()


def run_rag(
    question: str,
    document_id: str | None = None,
    top_k: int | None = None,
    run_eval: bool = True,
) -> QueryResponse:
    if document_id and store.document_id != document_id:
        query_index(question, k=1, document_id=document_id)  # loads store

    if not store.indexed:
        raise RuntimeError(NO_DOCUMENT_MSG)

    route = route_query(question)
    logger.info("Route: %s sub_questions=%s", route.query_type, route.sub_questions)

    pre, post = retrieve_and_rerank(question, route, top_k=top_k)
    answer = generate_answer(question, post)
    sources = _to_source_chunks(post)
    rerank_cmp = RerankComparison(
        pre_rerank=_to_source_chunks(pre[:10]),
        post_rerank=sources,
    )

    ragas: RagasScores | None = None
    if run_eval:
        contexts = [c.text for c, _ in post]
        ragas = compute_ragas_scores(question, answer, contexts)
        log_evaluation(
            question,
            answer,
            ragas,
            extra={
                "document_id": store.document_id,
                "route": route.model_dump(),
                "source_ids": [s.id for s in sources],
            },
        )

    return QueryResponse(
        answer=answer,
        sources=sources,
        route=route,
        rerank=rerank_cmp,
        ragas=ragas,
        document_id=store.document_id,
    )
