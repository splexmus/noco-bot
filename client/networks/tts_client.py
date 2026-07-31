import numpy as np

from .api_client import APIClient
from client.config import BASE_URL

class TTSClient(APIClient):

    def __init__(self):
        super().__init__(BASE_URL)

    def synthesize(self, text: str) -> np.ndarray:

        audio_bytes = self.post(
            endpoint="/tts",
            json={"text": text},
            response_type="bytes",
        )

        audio = np.frombuffer(
            audio_bytes,
            dtype=np.int16,
        ).copy()

        return audio