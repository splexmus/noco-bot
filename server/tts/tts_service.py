from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
import numpy as np
import io

from server.tts.piper_engine import PiperEngine

class TTSRequest(BaseModel):
    text: str


router = APIRouter()
tts = PiperEngine()


@router.post("/tts", tags=["tts"])
async def text_to_speech(request: TTSRequest):

    audio = tts.text_to_speech(request.text)

    buffer = io.BytesIO()
    np.save(buffer, audio)
    payload = buffer.getvalue()

    return Response(
        content=payload,
        media_type="application/octet-stream",
    )