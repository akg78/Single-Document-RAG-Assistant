"""Pydantic request / response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class SourceChunk(BaseModel):
    id: str
    page: int
    chunk_index: int
    snippet: str
    score: float | None = None
    source: str | None = None


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    num_pages: int
    num_chunks: int
    message: str = "Document indexed successfully"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: str | None = None
    top_k: int | None = None


class QueryRouteInfo(BaseModel):
    query_type: Literal["single_fact", "multi_part", "summarization"]
    sub_questions: list[str] = Field(default_factory=list)


class RerankComparison(BaseModel):
    """Before/after ordering for README demos and debugging."""

    pre_rerank: list[SourceChunk]
    post_rerank: list[SourceChunk]


class RagasScores(BaseModel):
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    route: QueryRouteInfo
    rerank: RerankComparison | None = None
    ragas: RagasScores | None = None
    document_id: str | None = None


class SuggestionsRequest(BaseModel):
    document_id: str | None = None
    n: int = Field(default=5, ge=1, le=10)


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class TopicsRequest(BaseModel):
    document_id: str | None = None


class TopicsResponse(BaseModel):
    topics: list[str]


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class EvaluateRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None


class EvaluateResponse(BaseModel):
    metrics: RagasScores
    logged: bool = True


class DocumentStatus(BaseModel):
    document_id: str | None
    filename: str | None
    num_chunks: int
    indexed: bool
    meta: dict[str, Any] = Field(default_factory=dict)
