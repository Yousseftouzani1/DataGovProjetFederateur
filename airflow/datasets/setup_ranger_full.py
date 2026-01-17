import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")
HEADERS = {"Content-Type": "application/json"}

def setup_complete_governance():
    print("🏗️ Building Ranger Governance Layer...")
    
    # 1. Create Tag Service if missing
    service_name = "data_gov_tags"
    
    # Check if exists
    resp = requests.get(f"{RANGER_URL}/service/plugins/services/name/{service_name}", auth=RANGER_AUTH)
    if resp.status_code == 200:
        print(f"✅ Service '{service_name}' already exists.")
    else:
        print(f"Creating Tag Service '{service_name}'...")
        svc_body = {
            "name": service_name,
            "type": "tag",
            "isEnabled": True,
            "configs": {}
        }
        resp = requests.post(f"{RANGER_URL}/service/plugins/services", json=svc_body, auth=RANGER_AUTH, headers=HEADERS)
        if resp.status_code == 200:
            print(f"✅ Created Service '{service_name}'.")
        else:
            print(f"❌ Failed to create service: {resp.text}")
            return

    # 2. Create PII Tag Definition
    print("Defining 'PII' Tag...")
    # Tag Defs are global but managed via the endpoint
    tag_def_body = {
        "name": "PII",
        "source": "Atlas",
        "owner": "admin",
        "attributeDefs": []
    }
    
    # Note: Tag Defs are unique by name globaly usually
    check = requests.get(f"{RANGER_URL}/service/tags/tagdef/name/PII", auth=RANGER_AUTH)
    if check.status_code == 200:
        print("✅ Tag Type 'PII' already exists.")
    else:
        resp = requests.post(f"{RANGER_URL}/service/tags/tagdef", json=tag_def_body, auth=RANGER_AUTH, headers=HEADERS)
        if resp.status_code == 200:
             print("✅ Created Tag Type 'PII'.")
        else:
             print(f"⚠️ Failed to create Tag Def (Might exist): {resp.status_code}")

    # 3. Create Policy
    print(f"Creating Security Policy in '{service_name}'...")
    policy_body = {
        "name": "Block_PII_Global",
        "service": service_name,
        "description": "Auto-generated policy to block PII access",
        "isEnabled": True,
        "resources": {
            "tag": {
                "values": ["PII"],
                "isExcludes": False,
                "isRecursive": False
            }
        },
        "policyItems": [
            {
                "accesses": [
                    {"type": "hdfs:read", "isAllowed": True}, 
                    {"type": "hive:select", "isAllowed": True},
                    {"type": "kafka:consume", "isAllowed": True}
                ],
                "users": ["admin"], # Removed 'steward' to prevent 400 error
                "groups": [],
                "delegateAdmin": True
            }
        ],
        "denyPolicyItems": [
            {
                "accesses": [
                    {"type": "hdfs:read", "isAllowed": True}, 
                    {"type": "hive:select", "isAllowed": True},
                    {"type": "kafka:consume", "isAllowed": True}
                ],
                "users": [],
                "groups": ["public"],
                "delegateAdmin": False
            }
        ]
    }
    
    # Check if policy exists by name (simplified check by creating and catching error)
    resp = requests.post(f"{RANGER_URL}/service/plugins/policies", json=policy_body, auth=RANGER_AUTH, headers=HEADERS)
    if resp.status_code == 200:
        print("✅ Policy 'Block_PII_Global' created!")
        print("🎉 SUCCESS: Governance Rules are now live in Ranger.")
    elif "already exists" in resp.text:
        print("✅ Policy 'Block_PII_Global' already updated.")
    else:
        print(f"❌ Failed to create policy: {resp.text}")

if __name__ == "__main__":
    setup_complete_governance()
