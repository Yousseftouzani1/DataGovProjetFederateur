import requests

RANGER_URL = "http://192.168.110.132:6080/service/public/v2/api/policy"
RANGER_AUTH = ("admin", "hortonworks1")

def prove_ranger_hive():
    print("--- 🔬 Injecting Ranger Hive Proof ---")
    payload = {
        "policyType": 0,
        "name": "ENSIAS_FINAL_AUDIT_POLICY",
        "service": "Sandbox_hive",
        "description": "Proof of real integration.",
        "isEnabled": True,
        "resources": {
            "database": {"values": ["ensias_audit_db"], "isExcludes": False, "isRecursive": False},
            "table": {"values": ["*"], "isExcludes": False, "isRecursive": False},
            "column": {"values": ["*"], "isExcludes": False, "isRecursive": False}
        },
        "policyItems": [
            {
                "accesses": [{"type": "select", "isAllowed": True}],
                "users": ["admin"],
                "delegateAdmin": False
            }
        ]
    }
    
    try:
        resp = requests.post(RANGER_URL, json=payload, auth=RANGER_AUTH, timeout=15)
        if resp.status_code in [200, 201]:
            print("✅ Ranger Hive Injection: SUCCESS")
            print("   Go to Ranger UI -> Hive -> Search 'ENSIAS'!")
        else:
            print(f"❌ Ranger Hive Injection: FAILED ({resp.status_code})")
            print(resp.text)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    prove_ranger_hive()
