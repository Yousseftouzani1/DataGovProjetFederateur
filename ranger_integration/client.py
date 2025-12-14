# ranger_integration/client.py

import requests
from ranger_integration.config import RANGER_CONFIG

class RangerClient:
    def __init__(self):
        self.base_url = RANGER_CONFIG["BASE_URL"] + RANGER_CONFIG["API_PREFIX"]
        self.auth = (RANGER_CONFIG["USERNAME"], RANGER_CONFIG["PASSWORD"])
        self.timeout = RANGER_CONFIG["TIMEOUT"]
        self.headers = {"Content-Type": "application/json"}

    def post(self, endpoint: str, payload: dict):
        response = requests.post(
            self.base_url + endpoint,
            json=payload,
            headers=self.headers,
            auth=self.auth,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get(self, endpoint: str):
        response = requests.get(
            self.base_url + endpoint,
            auth=self.auth,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
