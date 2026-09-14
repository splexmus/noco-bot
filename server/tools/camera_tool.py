from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

import requests

from server.config import settings


JPEG_START = b"\xff\xd8\xff"
JPEG_END = b"\xff\xd9"


class CameraToolError(RuntimeError):
    """Raised when the server cannot obtain a usable robot camera image."""


@dataclass(frozen=True)
class CameraCapture:
    content: bytes
    content_type: str
    size_bytes: int
    sha256: str


class RobotCameraClient:
    """Fetch the latest camera JPEG exposed by the robot-side image API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_size_bytes: int = 10 * 1024 * 1024,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or settings.robot_api_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.camera_timeout_seconds
        self.max_size_bytes = max_size_bytes
        self.session = session or requests.Session()

    def capture(self) -> CameraCapture:
        try:
            response = self.session.post(
                f"{self.base_url}/camera/capture",
                timeout=self.timeout_seconds,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CameraToolError(f"Robot camera request failed: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        content_type = content_type.partition(";")[0].strip().lower()

        if content_type != "image/jpeg":
            raise CameraToolError("Robot camera did not return image/jpeg")
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError as exc:
                raise CameraToolError("Robot camera returned invalid metadata") from exc
            if declared_size < 0 or declared_size > self.max_size_bytes:
                raise CameraToolError("Robot camera image exceeds the size limit")

        content_buffer = bytearray()
        try:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if len(content_buffer) + len(chunk) > self.max_size_bytes:
                    raise CameraToolError(
                        "Robot camera image exceeds the size limit"
                    )
                content_buffer.extend(chunk)
        except requests.RequestException as exc:
            raise CameraToolError(f"Robot camera stream failed: {exc}") from exc
        content = bytes(content_buffer)

        if not content:
            raise CameraToolError("Robot camera returned an empty image")
        if not content.startswith(JPEG_START) or not content.endswith(JPEG_END):
            raise CameraToolError("Robot camera returned malformed JPEG data")

        return CameraCapture(
            content=content,
            content_type=content_type,
            size_bytes=len(content),
            sha256=sha256(content).hexdigest(),
        )
