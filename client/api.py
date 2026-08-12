from fastapi import FastAPI
from .api.image import image_service

app = FastAPI()
app.include_router(image_service.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

@app.get("/health")
async def health():
    return {"status": "ok"}
