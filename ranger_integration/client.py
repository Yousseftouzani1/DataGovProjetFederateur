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

        response.raise_for_status()
        return response.json()

    # =========================================================
    #  ENHANCED IMPLEMENTATION (migrated from common)
    # =========================================================

    def check_access(self, user: str, resource: str, action: str = "read", service_name: str = "datagov_hadoop") -> bool:
        """
        Check if user has access to resource
        """
        try:
            # Ranger REST API for access check
            policy_check = {
                "resource": {"path": resource},
                "accessType": action,
                "user": user,
                "context": {}
            }
            # Note: This endpoint varies by Ranger version and plugin (HDFS/Hive/etc)
            # Using generic policy check endpoint for the service
            endpoint = f"/service/{service_name}/policy/check"
            # Fallback to generic if service specific fails or simple check needed
            
            # For HDP Sandbox often /api/policy/check is used with explicit resource def
            # Adapting to match common/ranger_client logic but with flexible endpoint
            response = requests.post(
                f"{self.base_url}/api/policy/check", 
                json=policy_check, 
                auth=self.auth
            )
            
            if response.status_code == 200:
                return response.json().get("allowed", False)
            return False
            
        except Exception as e:
            # print(f"❌ Ranger Access Check Failed: {e}")
            return False

    def create_pii_masking_policy(self, dataset_name: str, pii_columns: list):
        """
        Create a masking policy for PII columns in a dataset.
        Uses ranger_integration.policies builders.
        """
        try:
            from ranger_integration.policies import build_masking_policy
            
            policy_payload = build_masking_policy(
                policy_name=f"pii-masking-{dataset_name}",
                database="datagovdb",
                table=dataset_name,
                columns=pii_columns,
                users=["data_labeler", "data_annotator"],
                mask_type="MASK"
            )
            
            return self.post("/api/policy", policy_payload)
            
        except Exception as e:
            # print(f"❌ Masking policy creation failed: {e}")
            return None
