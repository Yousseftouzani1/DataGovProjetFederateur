import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")

def setup_ranger_pii():
    print("🛠️ Configuring Ranger PII Policies...")

    # 1. Create PII Tag Definition
    tag_def_body = {
        "name": "PII",
        "source": "Atlas",
        "description": "Personally Identifiable Information (Auto-Created)",
        "attributeDefs": []
    }
    
    # Check if exists first
    check = requests.get(f"{RANGER_URL}/service/tags/tagdef/name/PII", auth=RANGER_AUTH)
    if check.status_code == 200:
        print("✅ PII Tag Definition already exists.")
    else:
        print("Creating PII Tag Definition...")
        resp = requests.post(f"{RANGER_URL}/service/tags/tagdef", json=tag_def_body, auth=RANGER_AUTH)
        if resp.status_code == 200:
            print("✅ Created 'PII' Tag Definition.")
        else:
            print(f"⚠️ Failed to create Tag Def: {resp.text}")

    # 2. Create Tag-Based Policy: "Deny PII for Public"
    # We need the 'tag' service name. Usually 'cm_tag' or similar cluster name based.
    # Let's list services to find the tag service
    svc_resp = requests.get(f"{RANGER_URL}/service/plugins/services", auth=RANGER_AUTH)
    services = svc_resp.json().get('services', [])
    tag_service_name = next((s['name'] for s in services if s['type'] == 'tag'), None)
    
    if not tag_service_name:
        print("❌ Could not find a Ranger Service of type 'tag'. Cannot create policy.")
        # Fallback names roughly
        tag_service_name = "cl1_tag" 
        print(f"⚠️ Attempting fallback service name: {tag_service_name}")
    
    print(f"Using Tag Service: {tag_service_name}")

    policy_body = {
        "name": "Block_PII_Access",
        "description": "Deny access to PII tagged data for everyone except admin",
        "service": tag_service_name,
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
                "accesses": [{"type": "hdfs:read", "isAllowed": True}, {"type": "hive:select", "isAllowed": True}],
                "users": ["admin"],
                "groups": [],
                "delegateAdmin": True
            }
        ],
        "denyPolicyItems": [
            {
                "accesses": [{"type": "hdfs:read", "isAllowed": True}, {"type": "hive:select", "isAllowed": True}],
                "users": [],
                "groups": ["public"],  # Block everyone else
                "delegateAdmin": False
            }
        ]
    }
    
    # Create Policy
    print("Creating 'Block_PII' Policy...")
    p_resp = requests.post(f"{RANGER_URL}/service/plugins/policies", json=policy_body, auth=RANGER_AUTH)
    if p_resp.status_code == 200:
        print("✅ Policy 'Block_PII_Access' created successfully!")
        print("   -> Effect: Any resource tagged 'PII' is now BLOCKED for group 'public'.")
    elif p_resp.status_code == 400 and "already exists" in p_resp.text:
         print("✅ Policy already exists.")
    else:
        print(f"⚠️ Failed to create Policy: {p_resp.status_code} - {p_resp.text}")

if __name__ == "__main__":
    setup_ranger_pii()
