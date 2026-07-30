from .api_client import APIClient
from client.config import BASE_URL

class ChatClient(APIClient):
    def __init__(self):
        super().__init__(BASE_URL)

    def chat(self, text):
        return self.post( 
                endpoint = "/chat",
                json={"text": text},
                headers = {"Content-Type": "application/json"}
                )