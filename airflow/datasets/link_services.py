import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")
HEADERS = {"Content-Type": "application/json"}

def link_services():
    print("🔌 Linking Hive to Tag Service...")
    
    # 1. Get current definition
    resp = requests.get(f"{RANGER_URL}/service/plugins/services/name/Sandbox_hive", auth=RANGER_AUTH)
    if resp.status_code != 200:
        print("Failed to fetch Hive details.")
        return
        
    hive_svc = resp.json()
    
    # 2. Update config
    if 'configs' not in hive_svc:
        hive_svc['configs'] = {}
        
    hive_svc['configs']['tagService'] = 'data_gov_tags'
    
    # 3. Push Update
    svc_id = hive_svc['id']
    update_resp = requests.put(f"{RANGER_URL}/service/plugins/services/{svc_id}", json=hive_svc, auth=RANGER_AUTH, headers=HEADERS)
    
    if update_resp.status_code == 200:
        print("✅ SUCCESS: Hive is now linked to 'data_gov_tags'.")
        print("   -> Policy Enforcement is ACTIVE.")
    else:
        print(f"❌ Update failed: {update_resp.text}")

if __name__ == "__main__":
    link_services()
