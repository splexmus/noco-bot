from fastapi import FastAPI

from .image import image_service

app = FastAPI(title="NOCO Robot Image Receiver")
app.include_router(image_service.router)


@app.get("/")
async def root():
    return {"service": "noco-image-receiver"}


@app.get("/health")
async def health():
    return {"status": "ok"}
