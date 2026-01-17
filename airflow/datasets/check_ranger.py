import requests
import json
import os

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")  # Correct Creds

def check_ranger_tags():
    print("🕵️‍♂️ Checking Ranger Tag Sync...")
    
    # 1. List Tag Definitions (Types)
    try:
        url = f"{RANGER_URL}/service/tags/tagdefs"
        resp = requests.get(url, auth=RANGER_AUTH, timeout=5)
        
        if resp.status_code == 404:
             print("❌ Ranger Tag Service not found via 404.")
        elif resp.status_code == 401:
             print("❌ Auth failed for Ranger.")
             return
        
        data = resp.json()
        print(f"✅ Connection Successful. Status: {resp.status_code}")
        print(f"debug: Data Type: {type(data)}")
        
        # Handle List vs Dict response
        tag_defs = []
        if isinstance(data, list):
            tag_defs = data
        else:
            tag_defs = data.get('tagDefs', [])
            
        print(f"debug: Found {len(tag_defs)} Tag Definitions")
        
        # Check if PII tag def exists
        pii_found = any(t.get('name') == 'PII' for t in tag_defs)
        
        if pii_found:
            print("✅ 'PII' Tag Definition found in Ranger!")
        else:
            print("⚠️ 'PII' Tag Definition NOT found. TagSync might be lagging.")
            
    except Exception as e:
        print(f"Critical Error: {e}")

    # 2. Check Actual Tags on Resources
    try:
        url = f"{RANGER_URL}/service/tags/tags"
        resp = requests.get(url, auth=RANGER_AUTH, timeout=5)
        tags = resp.json().get('tags', [])
        print(f"📊 Total Synced Tags: {len(tags)}")
        
        for t in tags[:5]: # Show first 5
            print(f" - Found Tag: {t['type']} (ID: {t['id']})")
            
    except Exception as e:
        print(f"Fetch Tags Error: {e}")

if __name__ == "__main__":
    check_ranger_tags()
