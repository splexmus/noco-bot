import io
import unittest

import numpy as np
from fastapi import HTTPException
from server.stt.stt_service import post_stt
from server.stt.whisper_engine import TranscriptionInfo, TranscriptionSegment


class FakeWhisper:
    def transcribe(self, audio):
        assert isinstance(audio, np.ndarray)
        return (
            [TranscriptionSegment(start=0.0, end=0.5, text="hello")],
            TranscriptionInfo(language="en", language_probability=1.0),
        )


class SttServiceTest(unittest.TestCase):
    def test_preserves_stt_response_contract(self):
        buffer = io.BytesIO()
        np.save(buffer, np.zeros(1_000, dtype=np.int16))

        response = post_stt(buffer.getvalue(), FakeWhisper())

        self.assertEqual(response.text, "hello")
        self.assertEqual(response.language, "en")
        self.assertEqual(response.segments[0].end, 0.5)

    def test_rejects_non_numpy_payload(self):
        with self.assertRaises(HTTPException) as context:
            post_stt(b"not numpy", FakeWhisper())

        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
