# ranger_integration/client.py

import requests
from ranger_integration.config import RANGER_CONFIG

class RangerClient:
    def __init__(self):
        base = RANGER_CONFIG["BASE_URL"]
        prefix = RANGER_CONFIG["API_PREFIX"]
        # Eviter le double-prefixage
        if base.endswith(prefix):
            self.base_url = base
        else:
            self.base_url = base + prefix
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
