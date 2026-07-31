from fastapi import FastAPI
from .stt import stt_service
from .chat import chat_service
from .tts import tts_service

app = FastAPI()
app.include_router(stt_service.router)
app.include_router(chat_service.router)
app.include_router(tts_service.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

@app.get("/health")
async def health():
    return {"status": "ok"}
