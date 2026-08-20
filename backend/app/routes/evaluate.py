"""POST /api/evaluate — run RAGAS (or heuristic) metrics on a sample."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import EvaluateRequest, EvaluateResponse
from app.services.evaluator import compute_ragas_scores, log_evaluation

router = APIRouter(prefix="/api", tags=["evaluate"])


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(body: EvaluateRequest) -> EvaluateResponse:
    metrics = compute_ragas_scores(
        question=body.question,
        answer=body.answer,
        contexts=body.contexts,
        ground_truth=body.ground_truth,
    )
    log_evaluation(body.question, body.answer, metrics, extra={"source": "evaluate_endpoint"})
    return EvaluateResponse(metrics=metrics, logged=True)
