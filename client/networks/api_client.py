import requests

class APIClient:

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def post(
        self,
        endpoint: str,
        data,
        headers=None
    ):

        response = requests.post(
            self.base_url + endpoint,
            data=data,
            headers=headers,
            timeout=300,
        )

        response.raise_for_status()

        return response.json()