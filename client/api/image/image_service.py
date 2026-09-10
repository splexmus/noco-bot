from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .image_engine import ImageEngine, InvalidImageError

router = APIRouter()
image_engine = ImageEngine()


class ImageResponse(BaseModel):
    status: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


@router.get("/image", tags=["image"])
async def get_image() -> FileResponse:
    """Return the JPEG currently stored beside this module."""
    try:
        image_engine.info()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image has been stored",
        ) from exc
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return FileResponse(
        image_engine.image_path,
        media_type="image/jpeg",
        filename=image_engine.image_path.name,
    )


@router.post(
    "/image",
    tags=["image"],
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_image(request: Request) -> ImageResponse:
    """Receive a JPEG from the central server and store it as img.jpg."""
    content_type = request.headers.get("content-type", "")

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > image_engine.max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Image is too large",
                )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length header",
            ) from exc

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > image_engine.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image is too large",
            )
        body.extend(chunk)

    try:
        image_info = image_engine.save(bytes(body), content_type)
    except InvalidImageError as exc:
        response_status = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if len(body) > image_engine.max_size_bytes
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=response_status, detail=str(exc)) from exc

    return ImageResponse(status="stored", **image_info.__dict__)
