import unittest

import requests

from server.tools.camera_tool import CameraToolError, RobotCameraClient


JPEG = b"\xff\xd8\xffcamera frame\xff\xd9"


class FakeResponse:
    def __init__(self, content=JPEG, content_type="image/jpeg", error=None):
        self.content = content
        self.headers = {
            "content-type": content_type,
            "content-length": str(len(content)),
        }
        self.error = error

    def raise_for_status(self):
        if self.error is not None:
            raise self.error

    def iter_content(self, chunk_size):
        yield from (
            self.content[index : index + chunk_size]
            for index in range(0, len(self.content), chunk_size)
        )


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, timeout, stream):
        self.calls.append((url, timeout, stream))
        return self.response


class RobotCameraClientTest(unittest.TestCase):
    def test_fetches_and_validates_latest_jpeg(self):
        session = FakeSession(FakeResponse())
        camera = RobotCameraClient(
            base_url="http://robot:8001/",
            timeout_seconds=2,
            session=session,
        )

        capture = camera.capture()

        self.assertEqual(capture.content, JPEG)
        self.assertEqual(capture.size_bytes, len(JPEG))
        self.assertEqual(
            session.calls,
            [("http://robot:8001/camera/capture", 2, True)],
        )

    def test_rejects_non_jpeg_response(self):
        camera = RobotCameraClient(
            session=FakeSession(FakeResponse(content_type="text/plain"))
        )

        with self.assertRaises(CameraToolError):
            camera.capture()

    def test_wraps_network_errors(self):
        error = requests.HTTPError("camera unavailable")
        camera = RobotCameraClient(session=FakeSession(FakeResponse(error=error)))

        with self.assertRaisesRegex(CameraToolError, "camera request failed"):
            camera.capture()


if __name__ == "__main__":
    unittest.main()
