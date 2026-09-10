from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile


JPEG_CONTENT_TYPE = "image/jpeg"
JPEG_START = b"\xff\xd8\xff"
JPEG_END = b"\xff\xd9"


class InvalidImageError(ValueError):
    """Raised when an image payload cannot be accepted."""


@dataclass(frozen=True)
class ImageInfo:
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


class ImageEngine:
    """Validate and store the image shown by the robot client."""

    def __init__(
        self,
        image_path: str | Path | None = None,
        max_size_bytes: int = 10 * 1024 * 1024,
    ) -> None:
        self.image_path = (
            Path(image_path)
            if image_path is not None
            else Path(__file__).resolve().with_name("img.jpg")
        )
        self.max_size_bytes = max_size_bytes

    def save(self, payload: bytes, content_type: str) -> ImageInfo:
        """Validate JPEG bytes and atomically replace the current image."""
        normalized_content_type = content_type.partition(";")[0].strip().lower()
        self._validate(payload, normalized_content_type)

        self.image_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="wb",
                dir=self.image_path.parent,
                prefix=f".{self.image_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_file.write(payload)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
                temporary_path = Path(temporary_file.name)

            temporary_path.replace(self.image_path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

        return self.info(payload)

    def info(self, payload: bytes | None = None) -> ImageInfo:
        if payload is None:
            if not self.image_path.is_file():
                raise FileNotFoundError(self.image_path)
            payload = self.image_path.read_bytes()
            self._validate(payload, JPEG_CONTENT_TYPE)

        return ImageInfo(
            filename=self.image_path.name,
            content_type=JPEG_CONTENT_TYPE,
            size_bytes=len(payload),
            sha256=sha256(payload).hexdigest(),
        )

    def _validate(self, payload: bytes, content_type: str) -> None:
        if content_type != JPEG_CONTENT_TYPE:
            raise InvalidImageError("Content-Type must be image/jpeg")
        if not payload:
            raise InvalidImageError("Image body must not be empty")
        if len(payload) > self.max_size_bytes:
            raise InvalidImageError(
                f"Image exceeds the {self.max_size_bytes}-byte limit"
            )
        if not payload.startswith(JPEG_START) or not payload.endswith(JPEG_END):
            raise InvalidImageError("Body is not a valid JPEG payload")
