"""POST /api/tts — lightweight text-to-speech (WAV via pyttsx3 if available)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models import TTSRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["tts"])


@router.post("/tts")
async def text_to_speech(body: TTSRequest) -> Response:
    """
    Returns audio/wav when pyttsx3 is available; otherwise 501 so the
    frontend can fall back to the Web Speech API.
    """
    try:
        import pyttsx3  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail="Server TTS unavailable; use browser speechSynthesis.",
        ) from exc

    try:
        engine = pyttsx3.init()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = Path(tmp.name)
        engine.save_to_file(body.text, str(path))
        engine.runAndWait()
        data = path.read_bytes()
        path.unlink(missing_ok=True)
        return Response(content=data, media_type="audio/wav")
    except Exception as exc:  # noqa: BLE001
        logger.exception("TTS failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
