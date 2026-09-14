import subprocess
import tempfile
import unittest
from pathlib import Path

from client.api.image.camera_engine import CameraCaptureEngine, CameraCaptureError
from client.api.image.image_engine import ImageEngine


JPEG = b"\xff\xd8\xffcamera frame\xff\xd9"


class FakeRunner:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


class CameraCaptureEngineTest(unittest.TestCase):
    def test_captures_and_stores_jpeg(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "img.jpg"
            runner = FakeRunner(
                subprocess.CompletedProcess([], returncode=0, stdout=JPEG, stderr=b"")
            )
            camera = CameraCaptureEngine(
                image_engine=ImageEngine(image_path),
                device="/dev/video-test",
                width=320,
                height=240,
                timeout_seconds=3,
                runner=runner,
            )

            content, info = camera.capture()

            self.assertEqual(content, JPEG)
            self.assertEqual(image_path.read_bytes(), JPEG)
            self.assertEqual(info.size_bytes, len(JPEG))
            command, options = runner.calls[0]
            self.assertIn("/dev/video-test", command)
            self.assertIn("320x240", command)
            self.assertEqual(options["timeout"], 3)

    def test_reports_ffmpeg_failure(self):
        runner = FakeRunner(
            subprocess.CompletedProcess(
                [], returncode=1, stdout=b"", stderr=b"camera unavailable"
            )
        )
        camera = CameraCaptureEngine(runner=runner)

        with self.assertRaisesRegex(CameraCaptureError, "camera unavailable"):
            camera.capture()

    def test_reports_capture_timeout(self):
        runner = FakeRunner(error=subprocess.TimeoutExpired("ffmpeg", 1))
        camera = CameraCaptureEngine(runner=runner)

        with self.assertRaisesRegex(CameraCaptureError, "timed out"):
            camera.capture()


if __name__ == "__main__":
    unittest.main()
