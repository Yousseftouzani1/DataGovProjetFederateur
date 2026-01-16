import requests
import json

# Connection Settings
ATLAS_URL = "http://192.168.110.132:21000/api/atlas/v2"
ATLAS_AUTH = ("admin", "ensias2025")

# Note: Port 6080 for Ranger
RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")

def prove_atlas():
    print("--- 🔬 Injecting Atlas Proof-of-Life ---")
    payload = {
        "entity": {
            "typeName": "DataSet",
            "attributes": {
                "qualifiedName": "audit.ensias_2025_is_real",
                "name": "ENSIAS_2025_AUDIT_SUCCESS",
                "description": "This entity proves the Atlas integration is NOT mocked.",
                "owner": "Antigravity_Agent"
            }
        }
    }
    
    try:
        resp = requests.post(f"{ATLAS_URL}/entity", json=payload, auth=ATLAS_AUTH, timeout=15)
        if resp.status_code in [200, 201, 202]:
            print("✅ Atlas SQL Injection: SUCCESS")
            print(f"   Go to Atlas UI -> Search 'ENSIAS' to see it!")
        else:
            print(f"❌ Atlas SQL Injection: FAILED ({resp.status_code})")
            print(resp.text)
    except Exception as e:
        print(f"❌ Atlas Error: {str(e)}")

def prove_ranger():
    print("\n--- 🔬 Injecting Ranger Proof-of-Life ---")
    # Correcting Ranger API path
    payload = {
        "policyType": 0,
        "name": "ENSIAS_INTEGRATION_AUDIT_POLICY",
        "service": "Sandbox_hadoop",
        "description": "Proof that the Python code can create real security policies.",
        "isEnabled": True,
        "resources": {
            "path": {
                "values": ["/tmp/audit_test_ensias"],
                "isExcludes": False,
                "isRecursive": False
            }
        },
        "policyItems": [
            {
                "accesses": [{"type": "read", "isAllowed": True}],
                "users": ["admin"],
                "delegateAdmin": False
            }
        ]
    }
    
    try:
        resp = requests.post(f"{RANGER_URL}/service/public/v2/api/policy", json=payload, auth=RANGER_AUTH, timeout=15)
        if resp.status_code in [200, 201, 202]:
            print("✅ Ranger Policy Injection: SUCCESS")
            print(f"   Go to Ranger UI -> Hadoop Service -> Policies and search 'ENSIAS'!")
        else:
            print(f"❌ Ranger Policy Injection: FAILED ({resp.status_code})")
            print(resp.text)
    except Exception as e:
        print(f"❌ Ranger Error: {str(e)}")

if __name__ == "__main__":
    prove_atlas()
    prove_ranger()
