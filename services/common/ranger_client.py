import os
import requests
from typing import Optional

class RangerClient:
    """
    Client for Apache Ranger (Access Control)
    Handles permission checks for resources.
    """
    
    def __init__(self, ranger_url: str = None):
        self.base_url = ranger_url or os.getenv("RANGER_URL", "http://ranger:6080/service/public/v2")
        self.auth = (os.getenv("RANGER_USER", "admin"), os.getenv("RANGER_PASSWORD", "admin"))
        self.mock_mode = os.getenv("MOCK_GOVERNANCE", "true").lower() == "true"
        
        if not self.mock_mode:
            print(f"👮 Apache Ranger Client initialized at {self.base_url}")
        else:
            print(f"⚠️ Apache Ranger Client running in MOCK mode")
    
    def check_access(self, user: str, resource: str, action: str = "read") -> bool:
        """
        Check if user has access to resource
        user: username (e.g. 'annotator1')
        resource: resource path or name (e.g. '/data/sensitive/file.csv')
        action: 'read', 'write', 'execute'
        """
        if self.mock_mode:
            # Simple mock logic based on common naming conventions
            # print(f"[MOCK RANGER] Check: {user} -> {action} -> {resource}")
            
            # Example Policy: 'external' cannot access 'critical'
            if "external" in user and "critical" in resource:
                return False
                
            return True
            
        try:
            # Ranger REST API for access check
            policy_check = {
                "resource": resource,
                "accessType": action,
                "user": user,
                "context": {}
            }
            # Note: This endpoint varies by Ranger version and plugin (HDFS/Hive/etc)
            # Using generic policy check endpoint
            resp = requests.post(f"{self.base_url}/api/policy/check", json=policy_check, auth=self.auth)
            
            if resp.status_code == 200:
                return resp.json().get("allowed", False)
            return False
            
        except Exception as e:
            print(f"❌ Ranger Access Check Failed: {e}")
            # Fail safe: deny access on error
            return False

    def create_policy(self, name: str, resources: dict, allow: list):
        """Create a new access policy (Admin only)"""
        # Out of scope for client usage usually, but useful for setup
        pass
