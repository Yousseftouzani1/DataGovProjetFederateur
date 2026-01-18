"""
Ranger Client for FastAPI Integration
=====================================
This module provides utilities to check user permissions against Apache Ranger
before returning sensitive data.

Per Cahier des Charges Section 3.6:
- FastAPI validates JWT → Extracts role
- Appel à Ranger REST API pour vérifier la politique
- Si autorisé, appliquer le niveau de masquage approprié
"""

import requests
import os
from typing import Optional, Dict, Any
from enum import Enum

# Configuration
RANGER_URL = os.getenv("RANGER_URL", "http://100.91.176.196:6080")
RANGER_USER = os.getenv("RANGER_USER", "admin")
RANGER_PASSWORD = os.getenv("RANGER_PASSWORD", "hortonworks1")


class AccessDecision(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    MASKED = "masked"


class RangerClient:
    """Client for Apache Ranger policy evaluation"""
    
    def __init__(self, base_url: str = RANGER_URL, user: str = RANGER_USER, password: str = RANGER_PASSWORD):
        self.base_url = base_url
        self.auth = (user, password)
        self.tag_service = "data_gov_tags"
    
    def check_access(self, username: str, resource_tag: str = "PII") -> Dict[str, Any]:
        """
        Check if a user has access to a resource with a specific tag.
        
        Args:
            username: The user requesting access
            resource_tag: The tag on the resource (default: PII)
            
        Returns:
            Dict with 'decision' (AccessDecision) and 'mask_type' if applicable
        """
        try:
            # Get all policies for our tag service
            resp = requests.get(
                f"{self.base_url}/service/plugins/policies",
                params={"serviceName": self.tag_service},
                auth=self.auth,
                timeout=5
            )
            
            if resp.status_code != 200:
                print(f"Ranger API error: {resp.status_code}")
                return {"decision": AccessDecision.DENIED, "reason": "Ranger unavailable"}
            
            policies = resp.json().get('policies', [])
            
            # Check policies in order:
            # 1. First check deny policies
            # 2. Then check allow policies
            # 3. Then check masking policies
            
            is_denied = False
            is_allowed = False
            mask_type = None
            
            for policy in policies:
                if not policy.get('isEnabled', False):
                    continue
                    
                # Check if this policy applies to the requested tag
                policy_tags = policy.get('resources', {}).get('tag', {}).get('values', [])
                if resource_tag not in policy_tags:
                    continue
                
                # Check deny items
                for deny_item in policy.get('denyPolicyItems', []):
                    if username in deny_item.get('users', []):
                        is_denied = True
                        break
                    if 'public' in deny_item.get('groups', []):
                        # User might be in public group
                        is_denied = True
                        
                # Check allow items
                for allow_item in policy.get('policyItems', []):
                    if username in allow_item.get('users', []):
                        is_allowed = True
                        is_denied = False  # Explicit allow overrides public deny
                        break
                
                # Check masking items (policyType == 1)
                if policy.get('policyType') == 1:
                    for mask_item in policy.get('dataMaskPolicyItems', []):
                        if username in mask_item.get('users', []):
                            mask_type = mask_item.get('dataMaskInfo', {}).get('dataMaskType', 'MASK')
            
            # Determine final decision
            if is_denied and not is_allowed:
                return {"decision": AccessDecision.DENIED, "reason": "User denied by policy"}
            
            if mask_type:
                return {"decision": AccessDecision.MASKED, "mask_type": mask_type}
            
            if is_allowed:
                return {"decision": AccessDecision.ALLOWED}
            
            # Default deny (no explicit allow found)
            return {"decision": AccessDecision.DENIED, "reason": "No explicit allow policy"}
            
        except Exception as e:
            print(f"Ranger check failed: {e}")
            return {"decision": AccessDecision.DENIED, "reason": str(e)}
    
    def apply_masking(self, data: Dict[str, Any], mask_type: str, pii_columns: list) -> Dict[str, Any]:
        """
        Apply masking to sensitive columns based on mask type.
        
        Args:
            data: The data record to mask
            mask_type: Type of masking (MASK, MASK_SHOW_LAST_4, MASK_HASH, MASK_NULL)
            pii_columns: List of column names that are PII
            
        Returns:
            Masked data record
        """
        masked_data = data.copy()
        
        for col in pii_columns:
            if col in masked_data and masked_data[col]:
                value = str(masked_data[col])
                
                if mask_type == "MASK":
                    masked_data[col] = "*" * len(value)
                elif mask_type == "MASK_SHOW_LAST_4":
                    masked_data[col] = "*" * (len(value) - 4) + value[-4:] if len(value) > 4 else "****"
                elif mask_type == "MASK_SHOW_FIRST_4":
                    masked_data[col] = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
                elif mask_type == "MASK_HASH":
                    import hashlib
                    masked_data[col] = hashlib.sha256(value.encode()).hexdigest()[:16]
                elif mask_type == "MASK_NULL":
                    masked_data[col] = None
                else:
                    masked_data[col] = "****"
        
        return masked_data


# Singleton instance for easy import
ranger_client = RangerClient()


# Example usage:
if __name__ == "__main__":
    client = RangerClient()
    
    print("Testing Ranger Permissions...")
    
    # Test admin
    result = client.check_access("admin", "PII")
    print(f"Admin: {result}")
    
    # Test steward
    result = client.check_access("steward1", "PII")
    print(f"Steward: {result}")
    
    # Test annotator
    result = client.check_access("annotator1", "PII")
    print(f"Annotator: {result}")
    
    # Test labeler
    result = client.check_access("labeler1", "PII")
    print(f"Labeler: {result}")
    
    # Test random user
    result = client.check_access("hacker_bob", "PII")
    print(f"Hacker: {result}")
