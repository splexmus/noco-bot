from __future__ import annotations

import io
from functools import lru_cache
from typing import Annotated

import numpy as np
from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from .whisper_engine import WhisperEngine


MAX_AUDIO_BYTES = 32 * 1024 * 1024


class Segment(BaseModel):
    start: float
    end: float
    text: str


class STTResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    segments: list[Segment]


router = APIRouter()


@lru_cache(maxsize=1)
def get_whisper() -> WhisperEngine:
    """Load the Hugging Face model on the first STT request."""
    return WhisperEngine()


@router.post("/stt", tags=["stt"], response_model=STTResponse)
def post_stt(
    body: Annotated[bytes, Body(media_type="application/octet-stream")],
    whisper: WhisperEngine = Depends(get_whisper),
) -> STTResponse:
    if not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audio payload must not be empty",
        )
    if len(body) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio payload is too large",
        )

    try:
        audio = np.load(io.BytesIO(body), allow_pickle=False)
        if not isinstance(audio, np.ndarray):
            raise ValueError("Payload did not contain a NumPy array")
        segments, info = whisper.transcribe(audio)
    except (ValueError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid audio payload: {exc}",
        ) from exc

    response_segments = [
        Segment(start=segment.start, end=segment.end, text=segment.text)
        for segment in segments
    ]
    return STTResponse(
        text=" ".join(segment.text for segment in response_segments).strip(),
        segments=response_segments,
        language=info.language,
        language_probability=info.language_probability,
    )
