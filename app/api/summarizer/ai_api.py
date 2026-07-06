import requests


class AIAPI:
    BASE_URL = "http://127.0.0.1:8000"

    @staticmethod
    def post(endpoint: str, data: dict, token: str):
        response = requests.post(
            f"{AIAPI.BASE_URL}{endpoint}",
            json=data,
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()