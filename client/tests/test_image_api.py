import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from starlette.requests import Request

from client.api.image import image_service
from client.api.image.image_engine import ImageEngine


JPEG_BYTES = b"\xff\xd8\xff\xe0NOCO test image\xff\xd9"


def make_request(body: bytes, content_type: str = "image/jpeg") -> Request:
    messages = [
        {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }
    ]

    async def receive():
        return messages.pop(0)

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/image",
            "headers": [
                (b"content-type", content_type.encode("ascii")),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        },
        receive,
    )


class ImageApiTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_engine = image_service.image_engine
        image_service.image_engine = ImageEngine(
            Path(self.temporary_directory.name) / "img.jpg",
            max_size_bytes=64,
        )

    def tearDown(self):
        image_service.image_engine = self.original_engine
        self.temporary_directory.cleanup()

    async def test_receive_and_read_image(self):
        response = await image_service.receive_image(make_request(JPEG_BYTES))

        self.assertEqual(response.status, "stored")
        self.assertEqual(response.size_bytes, len(JPEG_BYTES))
        self.assertEqual(
            image_service.image_engine.image_path.read_bytes(), JPEG_BYTES
        )

        file_response = await image_service.get_image()
        self.assertEqual(Path(file_response.path).read_bytes(), JPEG_BYTES)
        self.assertEqual(file_response.media_type, "image/jpeg")

    async def test_rejects_non_jpeg_content_type(self):
        with self.assertRaises(HTTPException) as context:
            await image_service.receive_image(make_request(JPEG_BYTES, "image/png"))

        self.assertEqual(context.exception.status_code, 422)

    async def test_rejects_invalid_jpeg_bytes(self):
        with self.assertRaises(HTTPException) as context:
            await image_service.receive_image(make_request(b"not a jpeg"))

        self.assertEqual(context.exception.status_code, 422)

    async def test_missing_image_returns_not_found(self):
        with self.assertRaises(HTTPException) as context:
            await image_service.get_image()

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
