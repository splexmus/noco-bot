import requests

class APIClient:

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def post(
        self,
        endpoint: str,
        data = None,
        json = None,
        headers = None,
        response_type="json",
    ):

        response = requests.post(
            self.base_url + endpoint,
            data=data,
            json=json,
            headers=headers,
            timeout=300,
        )

        response.raise_for_status()

        if response_type == "bytes":
            return response.content

        return response.json()