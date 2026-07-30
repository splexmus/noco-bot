from fastapi import FastAPI
from .stt import service

app = FastAPI()
app.include_router(service.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
