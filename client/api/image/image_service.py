from fastapi import APIRouter, Request
from .image_engine import ImageEngine
import numpy as np
import io
from pydantic import BaseModel

router = APIRouter()

@router.post("/image", tags=["stt"])
async def post_stt(request: Request):
    body = await request.body()
    
    return ""

