"""POST /api/topics — coarse topic list from indexed chunks."""

from __future__ import annotations

import re
from collections import Counter

from fastapi import APIRouter, HTTPException

from app.models import TopicsRequest, TopicsResponse
from app.services.document_processor import NO_DOCUMENT_MSG, store

router = APIRouter(prefix="/api", tags=["topics"])

STOP = {
    "the", "and", "for", "that", "with", "this", "from", "are", "was", "were",
    "have", "has", "had", "not", "but", "what", "when", "which", "their", "they",
    "been", "will", "would", "could", "should", "about", "into", "than", "then",
    "also", "such", "only", "other", "more", "some", "these", "those", "over",
}


@router.post("/topics", response_model=TopicsResponse)
async def topics(_body: TopicsRequest) -> TopicsResponse:
    if not store.indexed:
        raise HTTPException(status_code=400, detail=NO_DOCUMENT_MSG)

    counter: Counter[str] = Counter()
    for chunk in store.chunks[:200]:
        words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", chunk.text)
        for w in words:
            lw = w.lower()
            if lw not in STOP:
                counter[lw] += 1

    topics_list = [w.title() for w, _ in counter.most_common(12)]
    return TopicsResponse(topics=topics_list)
