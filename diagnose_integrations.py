import requests
import os

# Configuration (Manually verified from user context)
ATLAS_URL = "http://192.168.110.132:21000/api/atlas/v2"
ATLAS_AUTH = ("admin", "ensias2025")

RANGER_URL = "http://192.168.110.132:6080/service/public/v2"
RANGER_AUTH = ("admin", "hortonworks1")

def test_atlas():
    print("--- Testing Atlas Connection ---")
    try:
        # Test basic types fetch
        resp = requests.get(f"{ATLAS_URL}/types/typedefs", auth=ATLAS_AUTH, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Atlas Integration: WORKING")
            print(f"Entities found: {len(resp.json().get('entityDefs', []))}")
        else:
            print(f"❌ Atlas Integration: FAILED (Auth or URL issue)")
    except Exception as e:
        print(f"❌ Atlas Integration: ERROR ({str(e)})")

def test_ranger():
    print("\n--- Testing Ranger Connection ---")
    try:
        # Test policies fetch
        resp = requests.get(f"{RANGER_URL}/api/service", auth=RANGER_AUTH, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Ranger Integration: WORKING")
            print(f"Services found: {len(resp.json())}")
        else:
            print(f"❌ Ranger Integration: FAILED (Auth or URL issue)")
    except Exception as e:
        print(f"❌ Ranger Integration: ERROR ({str(e)})")

if __name__ == "__main__":
    test_atlas()
    test_ranger()
