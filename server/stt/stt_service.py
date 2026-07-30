from fastapi import APIRouter, Request
from .whisper_engine import WhisperEngine
import numpy as np
import io
from pydantic import BaseModel

class Segment(BaseModel):
    start: float
    end: float
    text: str

class STTResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    segments: list[Segment]

whisper = WhisperEngine()
router = APIRouter()

@router.post("/stt", tags=["stt"], response_model=STTResponse)
async def post_stt(request: Request):
    body = await request.body()
    
    # 2. Wrap bytes in a memory buffer and load with NumPy
    buffer = io.BytesIO(body)
    arr = np.load(buffer)

    segments, info = whisper.transcribe(arr)

    result = []

    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
        })

    return {
        "text": " ".join(s["text"] for s in result),
        "segments": result,
        "language": info.language,
        "language_probability": info.language_probability,
    }