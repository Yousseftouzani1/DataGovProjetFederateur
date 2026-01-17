import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")

def check_hive_link():
    print("🕵️‍♂️ Checking connection between Hive and Tags...")
    
    # Get Hive Service Details
    try:
        resp = requests.get(f"{RANGER_URL}/service/plugins/services/name/Sandbox_hive", auth=RANGER_AUTH)
        if resp.status_code != 200:
            print("❌ Could not find 'Sandbox_hive' service.")
            return
            
        hive_svc = resp.json()
        linked_tag_svc = hive_svc.get('configs', {}).get('tagService')
        
        print(f"Hive Service: {hive_svc['name']}")
        print(f"Linked Tag Service: {linked_tag_svc}")
        
        if linked_tag_svc == 'data_gov_tags':
             print("✅ PERFECT LINK: Hive is listening to 'data_gov_tags'. Policies will work!")
        else:
             print("⚠️ BROKEN LINK: Hive is NOT listening to our new tag service.")
             print("   -> We need to update 'Sandbox_hive' configuration.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_hive_link()
