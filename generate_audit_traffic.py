import requests
import time
import random

BASE_URL = "http://localhost:8004"

users = ["admin", "labeler", "annotator", "steward"]
actions = ["view", "edit", "export"]

print("🚀 Generating audit traffic...")

for i in range(10):
    user = random.choice(users)
    print(f"[{i+1}/10] Simulating action for {user}...")
    
    # 1. Check Permissions (Logs to Mongo)
    try:
        requests.get(f"{BASE_URL}/permissions", params={"username": user, "role": "unknown"})
    except:
        pass
        
    time.sleep(0.5)

print("✅ Traffic generation complete.")
