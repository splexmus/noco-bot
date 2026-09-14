from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Sequence

from .image_engine import ImageEngine, ImageInfo


class CameraCaptureError(RuntimeError):
    """Raised when the robot camera cannot produce a JPEG frame."""


class CameraCaptureEngine:
    """Capture one V4L2 camera frame through ffmpeg and store it as img.jpg."""

    def __init__(
        self,
        image_engine: ImageEngine | None = None,
        device: str | None = None,
        width: int | None = None,
        height: int | None = None,
        timeout_seconds: float | None = None,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        self.image_engine = image_engine or ImageEngine()
        self.device = device or os.getenv("CAMERA_DEVICE", "/dev/video0")
        self.width = width or int(os.getenv("CAMERA_WIDTH", "640"))
        self.height = height or int(os.getenv("CAMERA_HEIGHT", "480"))
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("CAMERA_CAPTURE_TIMEOUT_SECONDS", "10")
        )
        self.runner = runner

    def capture(self) -> tuple[bytes, ImageInfo]:
        command = self.command()
        try:
            result = self.runner(
                command,
                capture_output=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise CameraCaptureError("ffmpeg is not installed") from exc
        except subprocess.TimeoutExpired as exc:
            raise CameraCaptureError("Camera capture timed out") from exc

        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise CameraCaptureError(error or "ffmpeg camera capture failed")

        content = bytes(result.stdout)
        try:
            info = self.image_engine.save(content, "image/jpeg")
        except ValueError as exc:
            raise CameraCaptureError(f"Camera produced an invalid JPEG: {exc}") from exc
        return content, info

    def command(self) -> Sequence[str]:
        return [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "v4l2",
            "-video_size",
            f"{self.width}x{self.height}",
            "-i",
            self.device,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "pipe:1",
        ]
