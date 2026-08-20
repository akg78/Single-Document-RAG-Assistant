"""POST /api/suggestions — suggested follow-up questions."""

from __future__ import annotations

from fastapi import APIRouter

from app.models import SuggestionsRequest, SuggestionsResponse
from app.services.document_processor import store

router = APIRouter(prefix="/api", tags=["suggestions"])


@router.post("/suggestions", response_model=SuggestionsResponse)
async def suggestions(body: SuggestionsRequest) -> SuggestionsResponse:
    n = body.n
    base = [
        "What is the main topic of this document?",
        "Summarize the key points in one paragraph.",
        "What definitions or terms are introduced?",
        "What conclusions does the author draw?",
        "Are there any important dates, figures, or metrics?",
        "What limitations or risks are mentioned?",
        "How does section 1 relate to later sections?",
        "What recommendations are made?",
    ]
    if store.filename:
        base.insert(0, f"Give an overview of '{store.filename}'.")
    return SuggestionsResponse(suggestions=base[:n])
