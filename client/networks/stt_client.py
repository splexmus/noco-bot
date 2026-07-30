import numpy as np
import io
from .api_client import APIClient
from client.config import BASE_URL

class STTClient(APIClient):
    def __init__(self):
        super().__init__(BASE_URL)

    def transcribe(self, audio):

        buffer = io.BytesIO()
        np.save(buffer, audio)
        payload = buffer.getvalue()

        return self.post( 
                endpoint = "/stt",
                data = payload,
                headers = {"Content-Type": "application/octet-stream"}
                )
