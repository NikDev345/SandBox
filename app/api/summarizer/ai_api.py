import requests
from config import *

class AIAPI:
    

    @staticmethod
    def post(endpoint: str, data: dict, token: str):
        response = requests.post(
            f"{APP_BASE_URL}{endpoint}",
            json=data,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()