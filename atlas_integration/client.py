# atlas_integration/client.py

import requests
from atlas_integration.config import ATLAS_CONFIG

class AtlasClient:
    def __init__(self):
        self.base_url = ATLAS_CONFIG["BASE_URL"] + ATLAS_CONFIG["API_PREFIX"]
        self.auth = (ATLAS_CONFIG["USERNAME"], ATLAS_CONFIG["PASSWORD"])
        self.timeout = ATLAS_CONFIG["TIMEOUT"]
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
